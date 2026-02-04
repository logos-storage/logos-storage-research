# Logos storage - an analysis of the file sharing components

### Research Objectives
This document contains an analysis of the Logos storage file sharing client. It is not a complete walkthrough of the whole codebase but rather looks at the overall architecture and how the components are connected to make up the whole system. The aim is to identify the information leakage in the protocol which require either changing the protocol or enhancing the protocol with an anonymization layer such as mixnet, onion routing, PIR, etc. We can summarize the research question as follows:
- **In the logos storage file sharing client, what PII are revealed to peers or to malicious external observer in the network?**

We start by going through the file sharing components and how they work, and then discuss the parts of the system that leaks PII and what requirements are needed (to be designed and implemented in future work) so that logos storage can achieve **private and anonymous file sharing**. 

**Note:** the analysis below is done on the existing codebase and since it going through improvements and optimizations in the next months, the implementation details might change but the overall architecture should remain the same. 

## Logos Storage - File Sharing Client

### Overview

Logos storage file sharing involves two main basic operations: (1) Publish/Upload (2) Download. 

Upload involves both initial upload of the data as well as serving the data to others (i.e. making it available for others to download), and these two are conceptually the same operation which will refer to as "publish/upload". Download is basically retrieving the data from local store and if not available, fetch it from peers in the network.

In order to achieve these two operations, we have 3 main components: (a) Discovery, (b) BlockStore, \(c) BlockExchange. 

- (a) Since it is a decentralized system, discovery with its DHT is needed so that nodes can find each other as well as find hosts for data blocks (and announcing that one is a host for specific blocks). 

- (b) The BlockStore is part of the system that handles storing the data locally which also includes chunking the data and possibly erasure coding and creating proofs. 

- \(c) The BlockExchange is the component responsible for exchanging (blocks) contents between peers in the network for both upload and download. 

Let's look at how these components interact with each other when publishing or downloading the data:

### (1) Publishing data
Publishing or uploading the data is done through the logos storage file sharing client/Node. The node publishes the data by first storing it locally (in the repostore as blocks) and then making it available to other peers in the network by announcing that the node has the data. Below is a diagram explaining the flow of the process.

<img src="./img/publish_flow.svg" alt="publish-diagram" style="width:100%; height:auto;">

**Publishing Flow**

1. User upload starts with the function `store(...)` in the node. The function chunks the input stream, hashes each chunk to create a block CID, and wraps bytes into a block.
2. Each block goes to `NetworkStore.putBlock(...)`. The networkStore stores the data locally and calls the blockexchange `resolveBlocks(...)` to signal to peers that the node has it and is no longer requesting it (if it was requested). Then the blockexchange will also start serving requests from peers that want the data.
3. The CIDs for the blocks are then used to build a Merkle tree resulting in a treeCID. Note that the hash used here is the SHA256 to build this tree. The networkStore then stores the key/values `(treeCid, index) -> proof` via `putCidAndProof(...)`.
4. Using the treeCID and other metadata (see manifest section below), the node also creates a manifest and stores it as a regular block by calling the `networkStore.putBlock(...)`.
5. On every successful `putBlock(...)`, if the Advertiser is running, `onBlockStored` is triggered for manifest CIDs ONLY and it calls `discovery.provide(..)` for both the manifest CID and the treeCid. This publishes provider records to the DHT.
6. At this point, the data is locally stored, proofs are recorded, blocks are marked available for peers, and discovery is advertising the manifest/tree for others to find. More info on blockStore and blockExchange in the next sections. 

**What is broadcasted on the network:**
We can observe that in the process of publishing data, the node calls two functions which interacts with the network. These are `blockexchange.resoveBlock(...)` in the blockexchange and `onBlockStored` in the advertizer. These serve and advertize to peers that the node has the data (or part of it) relating to the manifestCID and treeCID. We will look into these two functinos in more details later in this document to know exactly what information or PII these functions reveal. 

### (2) Downloading data
The downloading process is a result of user requesting data that is identified by a given manifestCID (or treeCID). The node would then try to serve the data if available locally, and if not, it will ask peers in the network for it. Peers will then serve it if they have it or save it in a `wantlist` for the asking peer and serve it later when it is available. 

For a full diagram of the downloading process, see [the diagram on mermaidchart](https://www.mermaidchart.com/app/projects/a2f6151f-76f9-4a74-9254-0cc4c24c5183/diagrams/f656a3e3-2301-4b87-a68f-5eb83c1c6d19/share/invite/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkb2N1bWVudElEIjoiZjY1NmEzZTMtMjMwMS00Yjg3LWE2OGYtNWViODNjMWM2ZDE5IiwiYWNjZXNzIjoiVmlldyIsImlhdCI6MTc2NjM5OTA3MX0.MOXbxlt3Yx4i4_QQMQ51i1aSdBu7KweVsoFEqrMwytc).

<img src="./img/download_flow.svg" alt="download-diagram" style="width:100%; height:auto;">

NOTES: the above diagram skips checks and other implementation specific steps since the purpose of it is to simplify how the download works and present an overview.

**Download flow**
Let's look in more detail at each step of the downloading process.
The node which is the main component does the following:

<p align="center">
  <img src="./img/node_flow.png" alt="node-diagram" width="400">
</p>

1. `retrieve(CID)`
User calls retrieve(CID) on the node to download content. The first thing the user needs is the CID for the content (manifestCid or single block CID) which can be distributed out-of-band or maybe stored locally. 
2. `Is manifest?`
Check if the CID is a manifest CID by matching the ManifestCodec with the given CID multicodec. If the CID is manifestCID then it is dataset not a single block and so it move forward with the `streamEntireDataset(...)`. If it is a single block, it just fetches that single block through `streamSingleBlock(...)`.
3. `fetchManifest(manifestCid)`
The node call `NetworkStore.getBlock(...)` which checks if the manifest block (the manifest has its own block) is available locally, if not, it triggers the blockexchange path (pending want + discovery + peer request) and the manifest is stored locally when delivered.
4. `Decode manifest`
Manifest is decoded to get its contents e.g. treeCid, blocksCount, etc.
5. `Iterate block indices` 
The node iterates block indices (via `fetchBatched`) for each index it builds a BlockAddress(treeCid, index) and calls `NetworkStore.getBlock(...)`. 
6. `Fetch single block`
Fetching each block requires calling the `networkStore.getblock(...)`. The networkStore is blockStore that basically tries to fetch blocks from local repoStore and if not found, requests the block from the blockexchange engine. When a block arrives, it's stored (using `putBlock(...)`) and `resolveBlocks(...)` clears the pending want, updates peers, and cancels requests. After all blocks are stored, the download completes. See the simplified diagram below for the blockstore interactions in the download process:

![blockstore-diagram](./img/blockstore_flow.png)

**What is broadcasted on the network:**
From the process of downloading the data, we can see that the node calls two functions which interact with the network. These are `blockexchange.requestBlock(address)` and `blockexchange.resoveBlock(...)` in the blockexchange. These functions and downstream functions interact with peers and might will reveal information about the node and the possibly the content. We will look into these two functions in more detail later in the document. 

## File Sharing Components 
Now let's look in more details at each of storage components in the following sections. 

### (a) Discovery
Discovery is the component that lets nodes: (1) **advertize** that they serve CIDs (for both contents with treeCid/manifestCid, and host addresses), (2) **lookup** other nodes that advertize some CIDs. In Logos storage, this is implemented using a modified Discv5 DHT

Discovery doesn't store raw CIDs as the DHT keys, but rather maps them to Discv5 nodeId keyspace using Keccak256. There are two objects to map:
- content CID -> nodeId
- host address -> nodeId

We can abstract the discovery with the following API calls:

```nim=
discovery.start() / discovery.stop()
```
Start/stop the underlying Discv5 based protocol engine. 

```nim=
discovery.provide(...)
```
The function takes either the content CID or host address (both mapped to nodeId). 
The main functionality is to advertize that "this node provides content/host_address  identified by this nodeId”

```nim=
discovery.find(...)
```
Again takes either CID or host address (peerId) also mapped to nodeId. Then look up providers for the nodeId. 

For more information, see the [DHT specs](https://lip.logos.co/storage/raw/dht). 

### (b) block store
The blockstore is an interface with a simple API. 
there are 3 main types of stores in codex that implement the blockstore: repoStore, cacheStore, and networkStore.

**blockStore interface**
Gets blocks and puts blocks based on the address which can be either a single block CID or (treeCid, index). The blockStore also stores and gets proofs for blocks.
Simplified interface:
```nim
getBlock(self, address: BlockAddress)
putBlock(self, blk: Block, ttl = Duration.none)
putCidAndProof(self, treeCid: Cid, index: Natural, blockCid: Cid, proof: CodexProof)
getCidAndProof(self, treeCid: Cid, index: Natural)
 ```   

**Block Merkle Trees and Proofs**
To build a merkle tree of the data blocks, you start by creating a CID for each block and then build a merkle tree on top of these CIDs resulting in a TreeCid which is later used to reference the whole dataset. Let's look at how that works in more detail.

**Blocks to CIDs**
The CIDs used in logos storage are based on the [libp2p CID implementation](https://github.com/vacp2p/nim-libp2p/blob/master/libp2p/cid.nim). 
A CID type contains:
```nim
  Cid* = object
    cidver*: CidVersion ## CID version
    mcodec*: MultiCodec ## CID mcodec identifier
    hpos*: int ## the offset in the CID’s data where the embedded multihash starts
    data*: VBuffer ## the hash digest blob
```

The `data` part of the CID contains `cidver||mcodec||multihash`
`multihash` comes from the output of multihash:
```nim!
  MultiHash* = object
    data*: VBuffer
    mcodec*: MultiCodec ## hash function identifier
    size*: int
    dpos*: int ## the byte offset of data where the digest bytes start
```
This `data` contains the concatenation: `mcodec||size||digest`. Note that the mcodec in the data blob is not the same as the cid mcodec. The `digest` part is the output of the specified hash function:
```nim!
mhash =? MultiHash.digest(hcodec, chunk)
```

**Merkle Tree (block CIDs -> TreeCID)**
Now to build a Merkle tree using the block cids, Logos storage uses a safe Merkle tree construction [(details of this are specified in here)](https://github.com/vacp2p/rfc-index/pull/281). The inner-working of the Merkle tree is outside of the scope of this document and so let's focus on what is the input and output of this merkle tree. 

The Merkle tree is built on top of the block CIDs that make up a dataset:
```nim!
tree =? CodexTree.init(cids)
```
Internally the function takes the `mcodec` to use for hashing, however, it strips out all the metadata in both the CID and Multihash (e.g. codec and size) and only builds the Merkle using the raw digest bytes as leaves. 
The TreeCID is then built using the tree root hash diest + CID metadata (mcodec, size, dpos). 

**CacheStore**
`cacheStore` is an in-memory LRU cache layer that implements `BlockStore`.
It is used for access to frequently used blocks.
It contains 2 caches:
- One for the data blocks so Cid -> block
- Another for mapping the (treeCid, index) -> proof

when getting/setting/deleting blocks or proofs, the store uses the 2 lrucache caches and return results. 

**networkStore**
`networkStore` is the one we mentioned earlier in the document and it is the one that interacts with the node. The networkStore delegates storage calls to local blockStore (e.g. RepoStore) and interacts with the network through the blockExchange, so it sits somewhere between the local and network storage. It tries to fetch data from local store (any store that impl blockstore can work but will most likely be the RepoStore) and if not available, goes to the blockExchange to request data from the network. On writes, the networkStore, calls the local store to write the data locally, and then notifies peers through the blockExchange that the node has the data + some cleanup. 

Notes: only the `getblock` gets the blocks from the network if not available locally. The `getCidAndProof(...)` is not requested from the network/blockexchange. This is because when the node gets the block through the blockExchange, the proof is expected to be delivered with the block. 

**RepoStore**
Repo store is the on-disk long-term storage. 
It interacts with [DataStore (DS)](https://github.com/logos-storage/nim-datastore/tree/master) as the backend which is (key,value) store, but that DS is pluggable so you can define the backend using it. The key in the store is the CID of the block or (treeCid,index). The implementation details of the repoStore is outside of the scope of this document and we can abstract it with only `getBlock(...)` and `putBlock(...)` to store and retrieve blocks from local storage. 

**RepoStore Metadata**
The RepoStore stores blocks as well as metadata for each block. The metadata are stored in a separate datastore called `metaDs` which is `TypedDatastore`. There is logic to add/delete/update data and metadata as neeeded.

This metadata contains:
```nim
BlockMetadata* {.serialize.} = object
    expiry*: SecondsSince1970
    size*: NBytes
    refCount*: Natural
```

as well as:

```nim
LeafMetadata* {.serialize.} = object
    blkCid*: Cid
    proof*: CodexProof
```

and:
```nim
  QuotaUsage* {.serialize.} = object
    used*: NBytes
    reserved*: NBytes
```

**BlockMaintainer**
The repo store has maintainace engine (BlockMaintainer) which iterate over the blocks and deletes expired ones, repeats every specified interval. 


**Discovery Datastore**
This is just LevelDB instance created for the DiscV5 discovery stack. It's separate from the repo store. It contains the DHT/provider state used by the discovery protocol (provider records for CIDs/hosts, etc.) so those records persist across restarts and can be reused for lookups/announces. No content blocks or metadata live there. 

**PeerCtxStore**
This is an in-memory table of active block-exchange peers and their state containing `OrderedTable[PeerId, BlockExcPeerCtx]`. It tracks each connected peer's wants/haves in `BlockExcPeerCtx`. This store also has logic to get and set each peers wants and haves. This is in-memory so it doesn't persist. It is used by the blockExchange and discovery (including advertizer). 

**Manifest**
The manifest contains metadata info on the dataset which includes:

```nim!
type Manifest* = ref object of RootObj
  treeCid {.serialize.}: Cid # Root of the merkle tree
  datasetSize {.serialize.}: NBytes # Total size of all blocks
  blockSize {.serialize.}: NBytes
    # Size of each contained block (might not be needed if blocks are len-prefixed)
  codec: MultiCodec # Dataset codec
  hcodec: MultiCodec # Multihash codec
  version: CidVersion # Cid version
  filename {.serialize.}: ?string # The filename of the content uploaded (optional)
  mimetype {.serialize.}: ?string # The mimetype of the content uploaded (optional)
```
For more information, see [the manifest specs](https://github.com/logos-storage/logos-storage-docs-obsidian/blob/main/10%20Notes/Specs/Codex%20Manifest%20Spec.md) and [research post: Reducing Metadata Overhead](https://github.com/logos-storage/logos-storage-research/blob/master/design/metadata-overhead.md). 

What is worth mentioning and not in the specs is that previously the manifest used to have a protected flag which is set to true for the erasure coded dataset manifest. This is because the manifest for the EC dataset is different than the non-EC one. However, we don't need to dig into the details of that so called "protected" manifest since it is deprecated/unused now after dropping erasure coding (for now). 

### \(c) Block exchange
The BlockExchange (`BlockExcEngine`) mediates between your BlockStore and peers in the network. The blockExchange is involved in both publishing and downloading content. In simple terms, during publishing as seen earlier in this document, the blockExchange informs peers that it has the data and serves that data. During download, the process is a bit more involved, so let's try to go through it. The flow can be simplified in the following diagram:

<img src="./img/blockexchange_flow.svg" alt="bx-diagram" style="width:100%; height:auto;">

**BlockExcEngine Flow**
1. The download process from the network starts with the networkStore calling the `requestBlock(address)` in the blockExchange. This starts the downloadInternal loop (retry loop). This loop will keep trying to get the data from peers with retry params set as:
```nim
const
  DefaultBlockRetries* = 3000
  DefaultRetryInterval* = 500.millis
```
Meaning that the node blockExchange will wait 500ms between every retry and will retry 3000 times. The `DefaultRetryInterval` param was later changed to 2 sec so it is less aggressive. 
2. In every retry attempt, the engine will check its knowledge of which peers have the content by calling `peerStore.getPeersForBlock(address)`. This function splits peers into those who have the content and those who don't:
```nim!
PeersForBlock* = tuple[with: seq[BlockExcPeerCtx], without: seq[BlockExcPeerCtx]]
```
3. For peers that we already know "have" the address, `sendWantBlock` is sent, which is to say to them "please send me the block". For others, `sendWantHave` advertises our interest in the data. 
4. If we don’t know any peer with it, the discovery engine will be invoked so that it queries the DHT to learn providers and update want lists. 
5. The engine keeps watching incoming wantlists from peers and update per-peer have/want sets. Incoming blocks arrive as `BlockDelivery` messages which are handled by `blocksDeliveryHandler`.
6. Each block that is part of a dataset i.e. a leaf of dataset tree that the engine receives `BlockDelivery` MUST include a Merkle proof matching treeCid/index, validation is done in `validateBlockDelivery`. Non-leaf deliveries just match CID.
7. On valid delivery, the engine stores the block via `localStore.putBlock(...)`. For leaves it also stores (treeCid, index) -> (blkCid, proof) via `putCidAndProof(...)`
8. After storing, `resolveBlocks(...)` is called which clears pending requests, cancels wantlists, and schedules serving peers that wanted these blocks
9. The underlying RepoStore's `onBlockStored` callback triggers the advertiser to announce manifest and tree CIDs.

Note: For more information see this [draft/raw blockexchange RFC](https://rfc.vac.dev/codex/raw/codex-block-exchange)

## Privacy and Anonymity - What leaks and where?
Let's look at what information is leaked during each operation (download & publish) and get a better understanding of the previously identified functions which interact with peers in the network. 

**Publish**
Publishing data requires two main interactions, the first is to announce that a dataset (a set of blocks identified by the manifest) is available i.e. to announce to other peers "I have CID X", and the second interaction is actually receiving requests from peers and sending the data. Let's look at these two interactions:
**`BlockStore.onBlockStored`**
This callback function is triggered once a block is stored in the local BlockStore, and it will then call the advertizer to:
- Checks if the stored CID is a manifest,
- and if it is a manifest then advertise the `manifestCID` and `TreeCID` via discovery `discovery.provide(cid: Cid)`.

From this we can see that only `manifestCID` and `TreeCID` reveal that the node is serving/publishing this dataset. Of course this only reveals that the node is publishing *some* dataset but only those who know what dataset this `manifestCID` and `TreeCID` refers to would know the exact dataset published. This is a problem for public data (i.e. data published to the public). 

Calling `discovery.provide(cid: Cid)` means that any DHT node that stores or forwards this update learns the content key (cid), provider identity (peerId), and the provider’s reachable address (multiaddrs).

**`blockexchange.resoveBlock(...)`**
Once the advertizer announces to peers that it has the dataset, the node also calls `blockexchange.resoveBlock(...)` so that the blockexchange engine can receive requests from peers and serve the data blocks. Through the blockexchange engine the node will receive wantlists containing `manifestCID` or `TreeCID` which contains the following:

```nim=
message Wantlist {
  enum WantType {
    wantBlock = 0;
    wantHave = 1;
  }

  message Entry {
    BlockAddress address = 1;
    int32 priority = 2;
    bool cancel = 3;
    WantType wantType = 4;
    bool sendDontHave = 5;
  }

  repeated Entry entries = 1;
  bool full = 2;
}

```

This is basically a list of `Entry` containing CIDs, and the request type: `wantBlock` you need the block data, `wantHave` only ask for the data. 

The publishing node will then serve either `BlockPresence` to say "I have dataset X":

```nim=
enum BlockPresenceType {
  presenceHave = 0;
  presenceDontHave = 1;
}

message BlockPresence {
  BlockAddress address = 1;
  BlockPresenceType type = 2;
  bytes price = 3;
}

```

Or the node will serve the actual data block:

```nim=
message BlockDelivery {
  bytes cid = 1;
  bytes data = 2;
  BlockAddress address = 3;
  bytes proof = 4;
}

```

Both receiving the requests, and serving them require some an anonymization layer in order to hide the publisher. 

**Download**
During download as seen earlier, the downloader node needs to call `blockexchange.requestBlock(address)`, which internally first finds peers that have data, by triggering `discovery.find(cid: Cid)` to get a list of peers that possibly have the data. Then, the node will send a block presence check (so called `wantHave`), i.e. to check if the peer actually has the data. Finally, the node will actually request the block data from the node(s) that responded. Once the download is complete, the node will store the data in the blockstore and call `blockexchange.resoveBlock(...)` which internally cancels the `wantHave` and `wantBlock` requests. See the figure below (from the blockexchange specs) which illustrates this. 

<img src="./img/download_msg_exchange.svg" alt="download-msg-diagram" style="width:100%; height:auto;">

`discovery.find(cid: Cid)`
Calls the discv5 protocol getProviders(nodeId) to retrieve provider records for that key/CID. When calling this function, DHT nodes on the lookup path learn you are querying/interested in this CID/key (i.e. interest in that dataset).
The node calling this function also learns a list of providers for the content and their addresses. 

**`blockexchange.requestBlock(...)`**

This functions leaks our interest in certain CIDs (or called addresses) since it sends the `WantList` to connected peers. The function not only leaks our interest to peers that has the data but also to those that don't (since in code we send wantHave to basically every peer we are connected with). 

In the request, the download node will send a wantlist with either `wantBlock` or `wantHave` as seen earlier. 

**`blockexchange.resoveBlock(...)`**
Once the download is complete, the node will (though `resoveBlock`) will send cancel requests to peers that it asked before, and start serving data. Note that the cancel request is yet another message that is sent to peers which reveal information and thus must be part of the messages sent over the anonymization layer. The logic following this is basically publishing the data as above. 


## Conclusion & Future work
In this analysis, we looked at how publishing and dowloading data works in the logos storage file-sharing client, with a focus on the interactions between the file-sharing components and the information exchanged between peers in the network. The file-sharing client as it stands now does not provide anonymity, and the next research step is to use the outcome of this analysis to design an anonymity layer on top of the file-sharing client to provide: (1) Anonymous download, (2) anonymous publishing. We have previously invetigated anonymous communication protocols in a previous research post ([Anonymity in Decentralized File Sharing](https://forum.vac.dev/t/anonymity-in-decentralized-file-sharing/628)) and we plan to research and specify how an anonymity protocol can be plugged into the logos storage file-sharing client. We plan to start with the [mix protocol (libp2p-mix)](https://lip.logos.co/ift-ts/raw/mix) since it offers the flexibity of building different types of mix networks (possibly with a TOR-like persistent circuit) and it can wrap around existing libp2p protocols. 

In the future, we will invetigate a complex set of protocol that provide stronger anonymity guarantees which include private information retrieval (PIR), Private discovery (DHT), etc.