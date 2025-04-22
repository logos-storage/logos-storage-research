# Threat Modeling

## Introduction

The goal of this threat modeling is to identify potential security vulnerabilities in
the Codex protocol, enabling us to take actions to mitigate them. Additionally, it can
serve as a starting point for directives in a security audit. The scope includes the
[Nim codebase](https://github.com/codex-storage/nim-codex) and the
[marketplace smart contracts](https://github.com/codex-storage/codex-contracts-eth).

## Methodology

The STRIDE framework is
used due to its simplicity and ability to quickly build an analysis.
The PASTA framework
was considered, but it is more business-oriented and suited for mature projects.
Additionally, its process is heavier than STRIDE's.

Threat modeling is an iterative process that requires constant updates as features are added or
modified in the codebase. Documenting potential security vulnerabilities helps developers
keep them in mind during code implementation.

DREAD is used as a risk assessment model to evaluate and prioritize security threats. Scores range is from 0 (low) to 10 (high).

Anyone is invited to contribute to this document, as it is a
collective effort rather than a one-person task.

### References

[Manifesto](https://www.threatmodelingmanifesto.org)  
[STRIDE](https://owasp.org/www-community/Threat_Modeling_Process#stride)  
[PASTA](https://cdn2.hubspot.net/hubfs/4598121/Content%20PDFs/VerSprite-PASTA-Threat-Modeling-Process-for-Attack-Simulation-Threat-Analysis.pdf)  
[DREAD](https://threat-modeling.com/dread-threat-modeling)

## Analysis

| Category               | Threat                                                  | Impact                            | Danger |
| ---------------------- | ------------------------------------------------------- | --------------------------------- | ------ |
| Spoofing               | [Phishing](#phishing)                                   | Financial, integrity              | ⚠️     |
| Spoofing               | [Same-Chain replay](#same-chain-replay)                 | Financial                         | 🛡️     |
| Spoofing               | [Cross-Chain replay](#cross-chain-replay)               | Financial                         | ⚠️     |
| Spoofing               | [API exposed](#api-exposed)                             | Abuse                             | ⚠️     |
| Tampering              | [Fake proofs](#fake-proofs)                             | Financial, disruptability         | 🛡️     |
| Tampering              | [Reentrancy](#Reentrancy)                               | Financial, integrity              | ⚠️     |
| Repudiation            | [Clever host](#clever-host)                             | Disruptability                    | 🛡️     |
| Information disclosure | [Data exposed](#data-exposed)                           | Reputation, privacy               | ⚠️     |
| Denial of service      | [Lazy host](#lazy-host)                                 | Disruptability                    | 🛡️     |
| Overload attack        | [Overload attack](#overload-attack)                     | Disruptability                    | ⚠️     |
| Denial of service      | [Lazy Client](#lazy-client)                             | Disruptability                    | 🛡️     |
| Denial of service      | [Censoring](#censoring)                                 | Censorship, disruptability, trust | 🛡️     |
| Denial of service      | [Greedy](#greedy)                                       | Unfairness, disruptability        | 🛡️     |
| Denial of service      | [Sticky](#sticky)                                       | Unfairness, centralization        | 🛡️     |
| Elevation of privilege | [Exploring a vulnerability](#exploring-a-vulnerability) | Financial, disruptability         | 🔥     |

## Spoofing

Threat action aimed at impersonating users or storage providers to access or manipulate
files and contracts in the network.

### Phishing

#### Scenario

When starting a Codex node, the user must load his private key to pay for initiating new
storage requests. This private key is stored in memory, and there is no authentication
process required to use the API. An attacker could reach the user via email phishing,
pretending to be from Codex. The email might redirect to a malicious website or include a
form that, upon the user's click, triggers a request to the Codex node to create a new storage request.

```
   ──────
 ─│      ─│              ┌────────────────┐
│           │            │                │
│ Attacker  │╶╶╶╶╶╶╶╶╶▶  │ Email phishing │
│           │            │                │
 ─│      ─│              └────────────────┘
   ──────                        ╷
      •                          ╷
      •                          ╷
      •                          ▼
      •                       ──────
      •                     ─│      ─│
      •                    │           │
      •                    │   User    │
      •                    │           │
      •                     ─│      ─│
      •                       ──────
      •                          ╷
      •                          ╷
      •                          ╷  Clicks on the phishing email
      •                          ╷
      •                          ╷
      •                          ▼
      •                  ┌────────────────┐
      •                  │                │
      •                  │ Unsecure form  │
      •                  │                │
      •                  └────────────────┘
      •                          ╷
      •                          ╷  Submits the form
      •                          ╷
      •                          ╷  action=/storage/request/CIDMalicious method=POST
      •                          ╷  input name="pricePerBytePerSecond" value="100000"
      •                          ▼
      •                  ┌────────────────┐
      •                  │                │
      •                  │  Codex node    │
      •                  │                │
      •                  └────────────────┘
      •                          ╷
      •                          ╷   POST /storage/request/CIDMalicious
      •                          ╷   pricePerBytePerSecond: 1000000
      •                          ╷
      •                          ▼
      •                  ┌────────────────┐
      •                  │                │
      •••••••••••••••••••│ Contract done  │
                         │                │
                         └────────────────┘
```

Edit/view: https://cascii.app/21c64

#### Impacts

This could lead to two issues:

- **Financial**: Malicious requests drain user wallet funds.
- **Integrity**: Attackers force the storage of insecure or illegal files via malicious CIDs,
  risking legal or reputational harm.

#### Mitigation

Typically, such web phishing attacks are mitigated by authentication or a
custom header to verify the request’s legitimacy.

However, Codex does not have an authentication mechanism, making options like CSRF
tokens impractical. Using a custom header would also provide a poor user experience
in Codex, as users would need to set the header manually, which is cumbersome and error-prone.

Users can reduce the risk of significant fund drainage by employing a hot wallet with
a small amount of tokens designated for storage requests, while keeping the majority
of their funds in a cold wallet. This limits the exposure to phishing attacks, as only
the tokens in the hot wallet are at risk. For example, a user might allocate just enough
tokens to cover typical storage needs, minimizing potential losses.

While this strategy mitigates the financial impact of unwanted storage requests, it does
not address the storage of unwanted or illegal content. An attacker could still trick the
user into storing harmful files via phishing.

#### DREAD score

| Component            | Score | Description                                                      |
| -------------------- | :---: | ---------------------------------------------------------------- |
| **Damage Potential** |   9   | Leads to fund loss and illegal content storage.                  |
| **Reproducibility**  |   8   | Easy to repeat once phishing is set up.                          |
| **Exploitability**   |   9   | Only requires a phishing form.                                   |
| **Affected Users**   |   7   | Targets many users running a node and unaware of security risks. |
| **Discoverability**  |   3   | Finding individual Codex users to contact is non-trivial.        |

**Average DREAD Score:** **7.2**

#### References

[CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#employing-custom-request-headers-for-ajaxapi)  
[Web 3 phishing attacks](https://drops.scamsniffer.io/scam-sniffer-2024-web3-phishing-attacks-wallet-drainers-drain-494-million/)

### Same-Chain replay

#### Scenario

An attacker captures a previously signed transaction and resends it on the same blockchain.
Because the signature is still valid, the transaction is accepted, and the attacker can drain the user's funds.

```
        ──────
    ─│──      ───│
     │           │
   │               │
   │     User      │
   │               │
     │           │
    ─│──      ───│
        ──────
           ╷
           ╷
           ╷
           ╷    Storage request
           ╷
           ╷
           ╷
           ▼
┌──────────────────────┐
│                      │
│     Codex node       │
│                      │
└──────────────────────┘
           ╷
           ╷
           ╷
           ▼
┌──────────────────────┐
│                      │
│  Request signature   │╶╶╶╶╶╶╶╶╶╶╶╶╶┐
│                      │             ╷
└──────────────────────┘             ╷
           ╷                         ╷
           ╷                         ▼
           ╷                      ──────
           ╷                    ─│      ─│
           ╷                   │           │
           ╷                   │ Attacker  │
           ╷                   │           │
           ╷                    ─│      ─│
           ╷                      ──────
           ▼                         ╷
┌──────────────────────┐             ╷
│                      │             ╷
│   Smart contract     │◀╶╶╶╶╶╶╶╶╶╶╶╶┘
│                      │
└──────────────────────┘
```

Edit/view: https://cascii.app/b28b7

#### Impacts

- **Financial**: Duplicate requests can drain user funds.

#### Mitigation

Include a unique, random `nonce` in the request data. This makes each signature unique and
prevents it from being reused on the same chain.

#### DREAD Score

| DREAD Component      | Score | Description                                          |
| -------------------- | :---: | ---------------------------------------------------- |
| **Damage Potential** |   8   | Can drain user funds through repeated transactions.  |
| **Reproducibility**  |   9   | Easy to repeat once a valid transaction is captured. |
| **Exploitability**   |   8   | Requires access to a signed transaction.             |
| **Affected Users**   |   9   | Affects any user sending signed requests.            |
| **Discoverability**  |   7   | Easy to try for the attacker.                        |

**Average DREAD Score:** **8.2**

#### References

[Quicknode](https://www.quicknode.com/guides/ethereum-development/smart-contracts/what-are-replay-attacks-on-ethereum#nonce)

### Cross-Chain replay

#### Scenario

An attacker captures a user’s signed transaction from a blockchain and replays it on
another chain that runs the same `Marketplace.sol` contract. Because the signature is
public and still valid, it can be used to replay the request and drain the user's funds.

```
        ──────
    ─│──      ───│
     │           │
   │               │
   │     User      │
   │               │
     │           │
    ─│──      ───│
        ──────
           ╷
           ╷
           ╷
           ╷    Storage request
           ╷
           ╷
           ╷
           ▼
┌──────────────────────┐
│                      │
│     Codex node       │
│                      │
└──────────────────────┘
           ╷
           ╷
           ╷
           ▼
┌──────────────────────┐
│                      │
│  Request signature   │
│                      │
└──────────────────────┘
           ╷
           ╷
           ╷
           ╷
           ▼
┌──────────────────────┐          ┌──────────────────────┐
│                      │          │                      │
│   Smart contract     │          │      Chain 1002      │
│                      │          │                      │
└──────────────────────┘          └──────────────────────┘
           ╷                                 ▲
           ╷                                 ╷
           ╷                                 ╷
           ╷                                 ╷
           ▼                               ──────
┌──────────────────────┐                 ─│      ─│
│                      │                │           │
│     Chain 1001       │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶ │ Attacker  │
│                      │                │           │
└──────────────────────┘                 ─│      ─│
                                           ──────


```

Edit/view: https://cascii.app/673f2

#### Impacts

- **Financial**: Replayed requests on another chain can drain user funds.

#### Mitigation

Implement EIP-712 to include chain-specific data in the signed transaction.
This ensures the signature is only valid on the intended chain and prevents unauthorized
replays on other chains.

#### DREAD Score

| DREAD Component      | Score | Description                                        |
| -------------------- | :---: | -------------------------------------------------- |
| **Damage Potential** |   8   | Can drain user funds across multiple chains.       |
| **Reproducibility**  |   5   | Needs two contract deployments on two blockchains. |
| **Exploitability**   |   7   | Needs access to a signed transaction.              |
| **Affected Users**   |  10   | Affects any user.                                  |
| **Discoverability**  |   7   | Easy to try for the attacker.                      |

**Average DREAD Score:** **7.4**

#### References

[Quicknode](https://www.quicknode.com/guides/ethereum-development/smart-contracts/what-are-replay-attacks-on-ethereum#chain-id)

### API exposed

#### Scenario

A user starts a node locally and sets `api-bindaddr` to `0.0.0.0`.
Worse, the user mistakenly enables port forwarding for the REST API as well.
As a result, the API is exposed, and an attacker can send any requests he wants.

```
                                     ──────
                                 ─│──      ───│
                                  │           │
                                │               │
           ┌╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶│     User      │╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┐
           ╷                    │               │                  ╷
           ╷                      │           │                    ╷
           ╷                     ─│──      ───│                    ╷
           ╷                         ──────                        ╷
           ╷                                                       ╷
           ╷ Starts with 0:0:0:0                  Enables port     ╷
           ╷                                      forwarding for   ╷
           ╷                                      REST api         ╷
           ╷                                                       ╷
           ╷                                                       ╷
           ▼                                                       ▼
┌──────────────────────┐                                ┌──────────────────────┐
│                      │                                │                      │
│      Codex node      │                                │      Codex node      │
│                      │                                │                      │
└──────────────────────┘                                └──────────────────────┘
           ▲                                                       ▲
           ╷                                                       ╷
           ╷                                                       ╷
           ╷                                                       ╷
           ╷                                                       ╷
           ╷                                                       ╷
        ──────                                                  ──────
      ─│      ─│                                              ─│      ─│
     │  Attacker │                                           │           │
     │  on same  │                                           │ Attacker  │
     │  network  │                                           │           │
      ─│      ─│                                              ─│      ─│
        ──────                                                  ──────
```

Edit/view: https://cascii.app/b762d

#### Impacts

- **Abuse**: Attackers can send API requests, draining funds or storing illegal content.

#### Mitigation

Educate users not to use `0.0.0.0` for `api-bindaddr` unless they fully understand the risks,
and to avoid enabling port forwarding for the API. A warning could be shown at startup
if `api-bindaddr` is not bound to `localhost`.

#### DREAD Score

| DREAD Component      | Score | Description                                    |
| -------------------- | :---: | ---------------------------------------------- |
| **Damage Potential** |  10   | Full API access.                               |
| **Reproducibility**  |   5   | Easy if node is misconfigured and exposed.     |
| **Exploitability**   |  10   | Needs no exploit.                              |
| **Affected Users**   |   2   | Affects users exposing their API by mistake.   |
| **Discoverability**  |   6   | Attackers can scan networks for exposed ports. |

**Average DREAD Score:** **6.6**

## Tampering

Threat action aimed at altering stored files, proofs, or smart contracts to disrupt
the network.

### Fake proofs

#### Scenario

If proof verification is weak and proofs can be submitted and verified too easily,
a storage provider could stop storing the data and attempt to send fake proofs,
claiming they are still hosting the content using the initial data they received.

```
         ──────
       ─│      ─│
      │           │
      │   User    │
      │           │
       ─│      ─│
         ──────
            ╷
  Storage   ╷
  Request   ╷
            ╷
            ▼
┌────────────────────────┐
│                        │
│      Codex network     │◀╶╶╶╶╶╶╶╶╶╶╶╶╶┐
│                        │              ╷
└────────────────────────┘
            ╷                   Delete the file
            ╷                   Submit fake proof
            ╷                           ╷
            ╷                           ╷
            ╷                           ╷
            ╷                           ╷
            ╷                           ▼
            ╷                        ──────
            ╷                      ─│      ─│
            ╷                     │           │
            ╷                     │    SP     │
            ╷                     │           │
            ╷                      ─│      ─│
            ╷                        ──────
            ╷                           ▲
            ╷                           ╷
            ╷                           ╷
            ╷                           ╷
            ╷                           ╷
            ╷                           ╷
            ╷                           ╷
            ▼                           ╷
 ┌────────────────────┐                 ╷
 │Slot 1│Slot 2│Slot 3│╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
 └────────────────────┘
```

Edit/view: https://cascii.app/cc7e0

#### Impacts

- **Financial**: Attackers try to earn contract rewards at the end of the contract without
  actually storing the file.
- **Disruptability**: The slot becomes unavailable from that storage provider,
  reducing network reliability.

#### Mitigation

Codex issues periodic random challenges, based on blockchain randomness, to verify that storage
providers still hold the data. Each failed challenge slashes the provider’s collateral. After multiple
failed proofs, the provider is removed from the contract, freeing the slot for another provider.

#### DREAD Score

| DREAD Component      | Score | Description                                        |
| -------------------- | :---: | -------------------------------------------------- |
| **Damage Potential** |   8   | Earns rewards without storing data.                |
| **Reproducibility**  |   6   | Easy if challenge system is weak or predictable.   |
| **Exploitability**   |   3   | Needs technical knowledge and protocol weaknesses. |
| **Affected Users**   |   5   | Impacts users who stored data on "attacker" hosts. |
| **Discoverability**  |   3   | Needs deep source code analysis to detect.         |

**Average DREAD Score:** **5.0**

#### References

[One File for the Price of Three: Catching Cheating Servers in Decentralized Storage Networks](https://web.archive.org/web/20240518000652/https://hackingdistributed.com/2018/08/06/PIEs/)

### Reentrancy

#### Scenario

The `markProofAsMissing` function, along with related functions such as `fillSlot` and `requestStorage`,
makes external calls (e.g., `transfer`) before completing internal state updates.
This opens the door to reentrancy attacks, where an attacker can re-enter the function and trigger
multiple operations in a single transaction, such as slashing collateral multiple times
or claiming validator rewards repeatedly.

```js
// Generated from slither report
Reentrancy in Marketplace.fillSlot(RequestId,uint64,Groth16Proof) (contracts/Marketplace.sol#187-251):
        External calls:
        - _transferFrom(msg.sender,collateralAmount) (contracts/Marketplace.sol#234)
                - ! _token.transferFrom(sender,receiver,amount) (contracts/Marketplace.sol#688)
        Event emitted after the call(s):
        - RequestFulfilled(requestId) (contracts/Marketplace.sol#249)
        - SlotFilled(requestId,slotIndex) (contracts/Marketplace.sol#241)
Reentrancy in Marketplace.markProofAsMissing(SlotId,Periods.Period) (contracts/Marketplace.sol#345-371):
        External calls:
        - ! _token.transfer(msg.sender,validatorRewardAmount) (contracts/Marketplace.sol#361)
        Event emitted after the call(s):
        - RequestFailed(requestId) (contracts/Marketplace.sol#407)
                - _forciblyFreeSlot(slotId) (contracts/Marketplace.sol#369)
        - SlotFreed(requestId,slot.slotIndex) (contracts/Marketplace.sol#396)
                - _forciblyFreeSlot(slotId) (contracts/Marketplace.sol#369)
Reentrancy in Marketplace.requestStorage(Request) (contracts/Marketplace.sol#132-177):
        External calls:
        - _transferFrom(msg.sender,amount) (contracts/Marketplace.sol#174)
                - ! _token.transferFrom(sender,receiver,amount) (contracts/Marketplace.sol#688)
        Event emitted after the call(s):
        - StorageRequested(id,request.ask,_requestContexts[id].expiresAt) (contracts/Marketplace.sol#176)
```

#### Mitigation

Apply the `Checks-Effects-Interactions` pattern.  
Use OpenZeppelin’s `ReentrancyGuard` to prevent nested entry into sensitive functions.

#### DREAD Score

| DREAD Component      | Score | Description                                           |
| -------------------- | :---: | ----------------------------------------------------- |
| **Damage Potential** |   8   | Can drain funds via multiple slashes and rewards.     |
| **Reproducibility**  |   2   | Works consistently if reentrancy is not prevented.    |
| **Exploitability**   |   2   | Requires contract-level knowledge and timing control. |
| **Affected Users**   |  10   | Affects any user.                                     |
| **Discoverability**  |   6   | Can be found through careful contract audit.          |

**Average DREAD Score:** **5**

#### References

[Solidity](https://docs.soliditylang.org/en/latest/security-considerations.html#reentrancy)  
[Checks-Effects-Interactions](https://docs.soliditylang.org/en/latest/security-considerations.html#use-the-checks-effects-interactions-pattern)  
[Reentrancy guard](https://docs.openzeppelin.com/contracts/4.x/api/security#ReentrancyGuard)

## Repudiation

Threat action aimed at denying responsibility for uploading files or agreeing to storage
contracts in the network.

### Clever host

#### Scenario

A storage provider can fill a slot and begin fulfilling its duties.
However, if a more profitable opportunity appears, the provider may abandon the first slot
in favor of the new one.

This behavior is not intended to harm the network but to pursue a better opportunity.
It is considered a form of repudiation, as the provider is effectively denying
its original commitment in order to prioritize another.

```
                        ──────
                      ─│      ─│
                     │           │
                     │   User    │
                     │           │
                      ─│      ─│                       ──────
                        ──────                       ─│      ─│
                           ╷                        │Better     │
                           ╷                        │Opportunity│
                           ╷                        │           │
                           ╷                         ─│      ─│
                           ▼                           ──────
                 ┌────────────────────┐                   ╷
                 │                    │                   ╷
                 │   Codex network    │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
                 │                    │
                 └────────────────────╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┐
                           ╷                                   ╷
                Request 1  ╷                                   ╷
                           ╷                                   ╷
                           ╷                                   ╷
                           ▼                                   ╷
                ┌────────────────────┐                         ╷
                │Slot 1│Slot 2│Slot 3│                         ╷
                └────────────────────┘                         ╷
                           ▲                                   ╷
                           ╷                                   ╷
Fill Request 1 Slot 2      ╷                                   ╷
                           ╷                                   ╷
                        ──────       Abandon Request 1 Slot 2  ╷
                    ─│──      ───│   to fill Request 2 Slot 2  ╷
                     │           │                             ▼
                   │               │                ┌────────────────────┐
                   │  Clever host  │╶╶╶╶╶╶╶╶╶╶╶╶╶▶  │Slot 1│Slot 2│Slot 3│
                   │               │                └────────────────────┘
                     │           │
                    ─│──      ───│
                        ──────
```

Edit/view: https://cascii.app/9e208

#### Impacts

- **Disruptability**: The slot becomes unavailable from that storage provider,
  reducing network reliability.

#### Mitigation

This attack is mitigated by the storage provider losing its request collateral for the first
slot once it is abandoned. Additionally, after filling the first slot, the rewards are only paid
out if the request is successfully completed. This delayed payout acts as an additional disincentive f
or the storage provider to abandon the slot.

#### DREAD Score

| DREAD Component      | Score | Description                                        |
| -------------------- | :---: | -------------------------------------------------- |
| **Damage Potential** |   5   | Reduces network reliability and causes slot waste. |
| **Reproducibility**  |   5   | Easy to repeat if better-paying slots are common.  |
| **Exploitability**   |   4   | Requires strategy but no technical exploit.        |
| **Affected Users**   |   4   | Affects clients relying on abandoned slots.        |
| **Discoverability**  |   3   | Hard to detect unless monitored closely.           |

**Average DREAD Score:** **4.2**

## Information disclosure

Information disclosure occurs when private or sensitive information such as user data,
file contents, or system secrets is unintentionally or maliciously revealed to unauthorized parties.

### Data exposed

#### Scenario

A user uploads a confidential file to Codex. Storage providers store unencrypted slots
of the file. Without encryption, providers could coordinate to gather these slots and
reassemble the full content.
Additionally, sensitive metadata, such as file location or identifiers, may be exposed.
Other users could access this information, creating a privacy risk.

```
                       ──────
                     ─│      ─│
                    │           │
                    │   User    │
                    │           │
                     ─│      ─│
                       ──────
                          ╷
          Upload a file   ╷
                          ╷
                          ▼           Access to the    ──────
                 ┌─────────────────┐  file metadata  ─│      ─│
                 │                 │                │           │
                 │      Codex      │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶│   User    │
                 │                 │                │           │
                 └─────────────────┘                 ─│      ─│
                          │                            ──────
                          │
                          │
                          ▼
               ┌────────────────────┐
      ┌╶╶╶╶╶╶╶╶│Slot 1│Slot 2│Slot 1│╶╶╶╶╶╶╶╶╶┐
      ╷        └────────────────────┘         ╷
      ╷                   ╷                   ╷
      ╷                   ╷                   ╷
      ▼                   ▼                   ▼
   ──────              ──────              ──────
 ─│      ─│          ─│      ─│          ─│      ─│
│           │       │           │       │           │
│    SP     │       │    SP     │       │    SP     │
│           │       │           │       │           │
 ─│      ─│          ─│      ─│          ─│      ─│
   ──────              ──────              ──────
     ╷                    ╷                    ╷
     ╷                    ╷                    ╷
     ╷                    ▼                    ╷
     ╷         ┌──────────────────────┐        ╷
     ╷         │                      │        ╷
     └╶╶╶╶╶╶▶  │     Original file    │ ◀╶╶╶╶╶╶┘
               │                      │
               └──────────────────────┘
```

Edit/view: https://cascii.app/7ff0e

#### Impacts

- **Reputation**: Codex cannot guarantee confidentiality, leading to a loss of
  trust in the protocol.
- **Privacy**: Exposure of sensitive user data could violate privacy and potentially
  result in legal or regulatory consequences.

#### Mitigation

Encrypt files to ensure that only authorized users can decrypt and access the contents.
In addition, sensitive metadata should be removed or encrypted where possible to reduce
the risk of privacy leaks.

#### DREAD Score

| DREAD Component      | Score | Description                                                     |
| -------------------- | :---: | --------------------------------------------------------------- |
| **Damage Potential** |   7   | Sensitive data or metadata may be publicly exposed.             |
| **Reproducibility**  |   4   | Easy if metadata are exposed, harder for full file content.     |
| **Exploitability**   |   2   | Requires file access and slot coordination.                     |
| **Affected Users**   |   7   | Affects users storing unencrypted or sensitive content.         |
| **Discoverability**  |   8   | Exposed content and metadata can be browsed in the source code. |

**Average DREAD Score:** **5.6**

References

[Metadata = Surveillance](https://www.schneier.com/blog/archives/2014/03/metadata_survei.html?utm_source=chatgpt.com)

## Denial of service

Threat action intended to make a service or resource unavailable to its intended users by overloading,
blocking, or disrupting normal operations.

### Lazy host

#### Scenario

In a single-reservation system, each slot is assigned to one storage provider through a 1-to-1 match.
A storage provider may reserve a slot but delay filling it, hoping a better opportunity will appear,
one that offers a higher reward than the original slot.

```
      ──────                                                ──────
    ─│      ─│                                            ─│      ─│
   │           │                                         │           │
   │   User    │                                         │   User    │
   │           │                                         │           │
    ─│      ─│                                            ─│      ─│
      ──────                                                ──────
         ╷                                                      ╷
         ╷                                                      ╷
         ╷                                                      ╷
         ╷                                                      ╷
         ╷                                                      ╷
         ╷               ┌────────────────────┐                 ╷
         ╷               │                    │                 ╷
         └╶╶╶╶╶╶╶╶╶╶╶╶▶  │   Codex network    │ ◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
                         │                    │
             ┌╶╶╶╶╶╶╶╶╶╶╶└────────────────────┘╶╶╶╶╶╶╶╶╶╶╶╶┐
             ╷                     ╷                       ╷
Request 1    ╷                     ╷                       ╷   Request 2
             ╷                     ╷                       ╷
             ╷                     ╷ Fill Request 2 Slot 2 ╷
             ▼                     ╷                       ▼
  ┌────────────────────┐           ╷            ┌────────────────────┐
  │Slot 1│Slot 2│Slot 3│           ╷            │Slot 1│Slot 2│Slot 3│
  └────────────────────┘           ╷            └────────────────────┘
             ╷                     ╷                        ╷
             ╷                     ╷                        ╷
             ╷                  ──────                      ╷
             ╷              ─│──      ───│                  ╷
             ╷               │           │                  ╷
             ╷             │               │                ╷
             └╶╶╶╶╶╶╶╶╶╶╶▶ │   Lazy host   │ ◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
                           │               │
Reserve Request 1 Slot 2     │           │      Reserve Request 2 Slot 2
                            ─│──      ───│
                                ──────
```

Edit/view: https://cascii.app/1f8a4

#### Impacts

- **Disruptability**: The storage request fails because the assigned storage provider
  chooses not to fill the slot, leaving it empty in favor of a better opportunity.

#### Mitigation

This attack is mitigated by allowing multiple reservations per slot.
Up to three storage providers can reserve the same slot and race to fill it.
If one or more providers choose to pursue other opportunities, the others can still
complete the request, ensuring reliability.

#### DREAD Score

| DREAD Component      | Score | Description                                                    |
| -------------------- | :---: | -------------------------------------------------------------- |
| **Damage Potential** |   7   | Fails storage requests.                                        |
| **Reproducibility**  |   8   | Easy to repeat if system allows only single reservations.      |
| **Exploitability**   |   3   | Requires strategic delay by the storage provider.              |
| **Affected Users**   |   4   | Affects users assigned to non-participating storage providers. |
| **Discoverability**  |   4   | Hard to detect until the storage deadline is missed.           |

**Average DREAD Score:** **5.2**

### Overload attack

#### Scenario

An attacker sends many small storage requests that generate a high volume of transactions.
This overloads validators and delays their ability to detect missed proofs in time.

```
                        ──────
                    ─│──      ───│
                     │           │
                   │               │
                   │   Attacker    │
                   │               │
                     │           │
                    ─│──      ───│
                        ──────
                           ╷
                           ╷    Small requests
                           ▼
          ┌─────────────────────────────────┐
          │R1│R2│R3│R4│R5│R5│R6│R7│R8│R9│R10│
          └─────────────────────────────────┘
            ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷    ╷
            ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷    ╷
            ╷  └╶╶└╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘╶╶┘    ╷
            ╷              ╷                ╷
            ╷              ▼                ╷
            ╷    ┌────────────────────┐     ╷
            ╷    │                    │     ╷
            └╶▶  │       Codex        │◀╶╶╶╶┘
                 │                    │
                 └────────────────────┘
                           ╷
                           ╷
                           ╷
                           ╷
     ──────                ╷               ──────
 ─│──      ───│            ╷           ─│──      ───│
  │           │    R1      ╷      R2    │           │
│               │          ╷          │               │
│   Validator   │ ◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶▶  │   Validator   │
│               │                     │               │
  │           │                         │           │
 ─│──      ───│                        ─│──      ───│
     ──────                                ──────

                Validators are too busy
```

Edit/view: https://cascii.app/3af32

#### Impacts

- **Disruptability**: Hosts might temporarily avoid penalties for not serving content,
  reducing file availability and causing users to lose trust in the Codex protocol.

#### Mitigation

Codex requires a small fee for each request, which helps limit spam.
Additional mitigations include optimizing the validation process to make proof checks faster,
limiting the number of storage requests per IP address, and setting a minimum file upload size.

#### DREAD Score

#### DREAD Score

| DREAD Component      | Score | Description                                            |
| -------------------- | :---: | ------------------------------------------------------ |
| **Damage Potential** |   8   | Temporarily weakens validation and file availability.  |
| **Reproducibility**  |   2   | Hard to repeat.                                        |
| **Exploitability**   |   2   | Requires ability to send many valid requests at scale. |
| **Affected Users**   |  10   | Affects all users.                                     |
| **Discoverability**  |   5   | Requires high activity.                                |

**Average DREAD Score:** **5.2**

### Lazy Client

#### Scenario

A client may try to disrupt the network by making storage requests but never provides
the actual data to the storage providers attempting to fill those slots.
As a result, the slots remain unfilled, wasting provider resources and delaying other requests.

```
                       ──────
                     ─│      ─│
                    │           │
                    │   User    │
                    │           │
                     ─│      ─│
                       ──────
                          ╷
          Upload a file   ╷
                          ╷
                          ▼
                 ┌─────────────────┐
                 │                 │
                 │      Codex      │
                 │                 │
                 └─────────────────┘
                          ╷
      Reservations        ╷
      without releasing   ╷
      data                ▼
               ┌────────────────────┐
      ┌╶╶╶╶╶╶╶╶│Slot 1│Slot 2│Slot 1│╶╶╶╶╶╶╶╶╶┐
      ╷        └────────────────────┘         ╷
      ╷                   ╷                   ╷
      ╷                   ╷                   ╷
      ▼                   ▼                   ▼
   ──────              ──────              ──────
 ─│      ─│          ─│      ─│          ─│      ─│
│           │       │           │       │           │
│    SP     │       │    SP     │       │    SP     │
│           │       │           │       │           │
 ─│      ─│          ─│      ─│          ─│      ─│
   ──────              ──────              ──────
```

Edit/view: https://cascii.app/c973a

#### Impacts

- **Disruptability**: Storage providers waste resources trying to store data that
  is never delivered, reducing the overall efficiency of the network.

#### Mitigation

The transaction cost for each storage request helps prevent this attack.
The more fake requests an attacker sends, the higher the total cost becomes due to
rising gas fees and block fill rates.
This makes it economically unfeasible to sustain large-scale spamming.

#### DREAD Score

| DREAD Component      | Score | Description                                                     |
| -------------------- | :---: | --------------------------------------------------------------- |
| **Damage Potential** |   5   | Wastes storage provider resources and slows the system.         |
| **Reproducibility**  |   2   | Possible but limited by transaction costs and network capacity. |
| **Exploitability**   |   2   | Requires funding.                                               |
| **Affected Users**   |   8   | Affects most users during periods of slot disruption.           |
| **Discoverability**  |   3   | Requires high activity.                                         |

**Average DREAD Score:** **4.0**

### Censoring

#### Scenario

A storage provider attempts to block access to specific CIDs in order to censor certain content.
This can also occur during the repair process, where the provider refuses to share the required
data, preventing a freed slot from being restored by others in the network.

```
                      ──────
                    ─│      ─│
                   │           │
                   │   User    │
                   │           │
                    ─│      ─│
                      ──────
                         ╷
         Upload a file   ╷
                         ╷
                         ▼
                ┌─────────────────┐
                │                 │
                │      Codex      │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶┐
                │                 │               ╷
                ╷─────────────────╷               ╷
                ╷                 ╷               ╷
                ╷                 ╷ Block the     ╷
Store the file  ╷                 ╷ content       ╷                  ──────
                ╷                 ╷         ┌───────────┐          ─│      ─│
                ╷     ──────      ╷         │           │         │           │
                ╷   ─│      ─│    ╷         │    CID    │◀╶╶╶╶╶╶╶╶│   User    │
                ╷  │           │  ╷         │           │         │           │
                └╶▶│    SP     │◀╶┘         └───────────┘          ─│      ─│
                   │           │                                     ──────
                    ─│      ─│
                      ──────
```

Edit/view: https://cascii.app/e1d00

#### Impacts

- **Censorship**: The storage provider may prevent users from accessing certain data,
  stopping them from retrieving content they need.
- **Disruptability**: If the storage provider blocks data during a repair,
  it could stop the network from restoring missing files, making the data unavailable.
- **Trust**: Users may lose trust in the network if they believe some providers
  can block or censor content.

#### Mitigation

Even if one storage provider withholds certain content, the dataset and the blocked CID
can be rebuilt using chunks from other providers. This means the censored CID can still
be accessed through other nodes, reducing the impact of the attack.

### Greedy

#### Scenario

A storage provider attempts to fill multiple slots in the same storage request by quickly submitting
multiple offers. This gives them a larger share of the deal, limiting participation by other providers.

```
                      ──────
                    ─│      ─│
                   │           │
                   │   User    │
                   │           │
                    ─│      ─│
                      ──────
                         ╷
         Upload a file   ╷
                         ╷
                         ▼
                ┌─────────────────┐
                │                 │
                │      Codex      │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶┐
                │                 │               ╷
                ╷─────────────────╷               ╷
                ╷                 ╷               ╷
                ╷                 ╷ Block the     ╷
Store the file  ╷                 ╷ content       ╷                  ──────
                ╷                 ╷         ┌───────────┐          ─│      ─│
                ╷     ──────      ╷         │           │         │           │
                ╷   ─│      ─│    ╷         │    CID    │◀╶╶╶╶╶╶╶╶│   User    │
                ╷  │           │  ╷         │           │         │           │
                └▶ │    SP     │◀╶┘         └───────────┘          ─│      ─│
                   │           │                                     ──────
                    ─│      ─│
                      ──────

```

Edit/view: https://cascii.app/279c5

#### Impacts

- **Unfairness**: Allows one provider to control more resources than intended, reducing fairness
  in slot allocation.
- **Disruptability**: Limits opportunities for other providers and reduces network decentralization.

#### Mitigation

The expanding window mechanism helps prevent this attack. It gradually opens slot availability to more
storage providers, making it harder for one to dominate all slots early. However, near the expiration of
the request, the mechanism may be less effective, as fewer providers may be available to fill new slots in time.

#### DREAD Score

| DREAD Component      | Score | Description                                                   |
| -------------------- | :---: | ------------------------------------------------------------- |
| **Damage Potential** |   5   | Reduces fairness, may lead to centralization over time.       |
| **Reproducibility**  |   6   | Easy to repeat with fast or automated submissions.            |
| **Exploitability**   |   2   | Requires timing advantage or faster infrastructure.           |
| **Affected Users**   |   6   | Affects any users sharing storage requests with greedy hosts. |
| **Discoverability**  |   4   | Can go unnoticed unless provider patterns are analyzed.       |

**Average DREAD Score:** **4.6**

### Sticky

#### Scenario

A storage provider tries to retain control of a storage slot during contract renewal.
They do this by withholding the data from other providers and waiting for the expanding
window to open. Since they already have the data, they can act faster than others
and fill the slot again before anyone else.

```
             ──────
           ─│      ─│
          │           │
          │   User    │
          │           │
           ─│      ─│
             ──────
                ╷
Upload a file   ╷
                ╷
                ▼
       ┌─────────────────┐
       │                 │
       │      Codex      │
       │                 │
       └─────────────────┘
                ╷
                ╷             ┌───────────────────────┐
                ╷             │                       │
 Store the file ╷             │    Contract renewal   │
                ╷             │                       │
                ╷             └───────────────────────┘
                ╷                         ▲
                ▼                         ╷
             ──────                       ╷
           ─│      ─│                     ╷
          │           │                   ╷
          │    SP     │╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
          │           │        Witholding data
           ─│      ─│          and wait for expanding
             ──────            window to open
```

Edit/view: https://cascii.app/db8fa

#### Impacts

- **Unfairness**: The storage provider gains an unfair advantage by renewing the
  contract without giving others a fair opportunity.
- **Centralization**: Can lead to fewer storage providers handling more data,
  making the network less balanced and more centralized.

#### Mitigation

This attack is difficult to succeed with unless the storage provider controls a large
portion of the network. The expanding window mechanism helps prevent this by spreading
out renewal opportunities and giving other providers a fair chance to fill the slots.

#### DREAD Score

| DREAD Component      | Score | Description                                              |
| -------------------- | :---: | -------------------------------------------------------- |
| **Damage Potential** |   5   | Unfair slot control but no direct loss.                  |
| **Reproducibility**  |   2   | Requires repeated timing success in renewal windows.     |
| **Exploitability**   |   2   | Hard with window mechanism.                              |
| **Affected Users**   |   6   | Users who renew the storage contract.                    |
| **Discoverability**  |   2   | Hard to detect unless slot filling is closely monitored. |

**Average DREAD Score:** **3.4**

## Elevation of privilege

Threat action intending to gain privileged access to resources in order to gain unauthorized access to information or to compromise a system.

### Exploring a vulnerability

#### Scenario

An attacker discovers a vulnerability in Codex’s smart contract after it is deployed.
Since anyone can interact with the contract, the attacker exploits the vulnerability to change
deal terms in their favor and take control of the funds.

```
                         ┌────────────────────────────┐
                         │                            │
                         │           Codex            │
                         │                            │
                         └────────────────────────────┘
                                       ╷
                                       ╷
                                       ╷   Deploy without ownership
                                       ╷
                                       ╷
  Take control of the s                ▼
  mart contracts         ┌───────────────────────────┐
                         │                           │
        ┌╶╶╶╶╶╶╶╶╶╶╶╶╶╶▶ │       Smart contracts     │
        ╷                │                           │
        ╷                ╷───────────────────────────┘
        ╷                ╷             ▲
        ╷                ╷             ╷
        ╷                ╷             ╷
        ╷                ╷             ╷
     ──────              ╷             ╷
 ─│──      ───│          ╷             ╷
  │           │          ╷             ╷
│               │        ╷             ╷
│   Attacker    │◀╶╶╶╶╶╶╶┘             ╷
│               │                      ╷
  │           │      Manipulates       ╷
 ─│──      ───│      incoming storage  ╷
     ──────          requests          ╷
                                       ╷
                                       ╷
                                       ╷
                                    ──────
                                ─│──      ───│
                                 │           │
                               │               │
                               │Storage request│
                               │               │
                                 │           │
                                ─│──      ───│
                                    ──────
```

Edit/view: https://cascii.app/4d5a6

#### Impacts

- **Financial**: Attackers could modify deals to steal funds or block payments.
- **Disruptability**: The integrity of the Codex protocol is compromised, leading to a loss of trust.

#### Mitigation

Use upgradable contracts to enable future fixes. Additionally, implement temporary admin roles
with multi-signature approval for changing critical settings or logic.

#### DREAD Score

| DREAD Component      | Score | Description                                                    |
| -------------------- | :---: | -------------------------------------------------------------- |
| **Damage Potential** |  10   | Full control over deal logic or funds.                         |
| **Reproducibility**  |   9   | Easy to repeat once the vulnerability is known.                |
| **Exploitability**   |   5   | Requires finding and triggering a public contract weakness.    |
| **Affected Users**   |  10   | Affects all users using the vulnerable contract.               |
| **Discoverability**  |   5   | Harder to find, but public contract code helps skilled actors. |

**Average DREAD Score:** **7.8**
