# Threat Modeling

## Introduction

The goal of this threat modeling is to identify potential security vulnerabilities in
the Codex protocol, enabling us to take actions to mitigate them. Additionally, it can
serve as a starting point for directives in a security audit. The scope includes the
[Nim codebase](https://github.com/codex-storage/nim-codex) and the
[marketplace smart contracts](https://github.com/codex-storage/codex-contracts-eth).

## Methodology

The [STRIDE][1] framework is used due to its simplicity and the ability to quickly build
an analysis.  
The [PASTA][2] framework was considered but is more business-oriented and suited for mature
projects. Additionally, its process is heavier than STRIDE's.

Threat modeling is an iterative process, requiring constant updates as features are added or
modified in the codebase. Documenting potential security vulnerabilities helps developers to
keep them in mind during the code implementation.

Anyone is invited to contribute to this document, as it is a
[collective effort](https://www.threatmodelingmanifesto.org) rather than a one-person task.

## Analysis

| Category               | Threat                                                            | Description                                                                                   | Impact                                                                      | Mitigation                                                 |
| ---------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Spoofing               | [Phishing-Induced spoofing](#phishing-induced-spoofing)           | Exploits the private key loaded directly into the app via phishing to send unwanted requests. | Draining the user's wallet funds, store unwanted content.                   | Use cold wallet.                                           |
| Spoofing               | [Same-Chain attack replays](#same-chain-attack-replays)           | Reuses a signed transaction on the same chain to spoof user actions.                          | Drained wallet funds.                                                       | Include a unique nonce in request data.                    |
| Spoofing               | [Cross-Chain attack replays](#cross-chain-attack-replays)         | Replays a signed transaction on another chain.                                                | Drained wallet funds.                                                       | Implement EIP-712.                                         |
| Spoofing               | [Client spoofing via API](#client-spoofing-via-api)               | Access to the exposed node to use the API.                                                    | Node full API access.                                                       | Educate users.                                             |
| Tampering              | [Fake proofs](#fake-proofs)                                       | The storage provider sends fake proofs.                                                       | Contracts reward without actual data storage, reducing network reliability. | Require random challenges periodically.                    |
| Tampering              | [markProofAsMissing re-entrency](#markproofasmissing-re-entrency) | The validator uses re-entrancy to slash multiple times.                                       | Excessive collateral slashing of the host, proof validation failure.        | Apply the `Checks-Effects-Interactions` pattern.           |
| Repudiation            | [Denial of file upload](#denial-of-file-upload)                   | User denies uploading illegal content.                                                        | Reputation impact and trust failure                                         | Make a clear legal statement.                              |
| Repudiation            | [Clever host](#clever-host)                                       | Storage provider abandon its duties for a better opportunity.                                 | Reduces network reliability.                                                | Slash collateral and reward repairing slot.                |
| Information disclosure | [Uploaded files exposed](#uploaded-files-exposed)                 | Non encrypted files can be reconstructed.                                                     | Reputation and privacy exposure.                                            | Add encryption layer.                                      |
| Elevation of privilege | [Exploring a vulnerability](#exploring-a-vulnerability)           | The attacker exploits a vulnerability to take over the smart contracts.                       | System Disruption.                                                          | Upgradable contracts and / or admin role.                  |
| Denial of service      | [Lazy host](#lazy-host)                                           | Host reserves a slot, but doesn't fill it                                                     | System Disruption.                                                          | Multiple reservations.                                     |
| Denial of service      | [Lazy host](#lazy-host)                                           | Host reserves a slot, but doesn't fill it                                                     | System Disruption.                                                          | Multiple reservations.                                     |
| Overload attack        | [Overload attack](#overload-attack)                               | Massive small requests to overload validators.                                                | System Disruption.                                                          | Client doesn't release content on the network.             |
| Denial of service      | [Lazy Client](#lazy-client)                                       | Starting request fees.                                                                        | System Disruption.                                                          | Transaction cost                                           |
| Denial of service      | [Censoring](#censoring)                                           | Acts like a lazy host for specific CIDs that it tries to censor fees.                         | System Disruption.                                                          | Dataset and CID and be rebuilt by other storage providers. |
| Denial of service      | [Greedy](#greedy)                                                 | Storage provider tries to fill multiple slots in a request                                    | System Disruption.                                                          | Expanding window mechanism                                 |
| Denial of service      | [Sticky](#sticky)                                                 | Storage provider tries to fill the same slot in a contract renewal.                           | System Disruption.                                                          | Expanding window mechanism                                 |

## Spoofing

Threat action aimed at impersonating users or storage providers to access or manipulate
files and contracts in the network.

### Phishing-Induced spoofing

#### Scenario

When starting a Codex node, the user must load his private key to pay for initiating new
storage requests. This private key is loaded into memory, and there is no authentication
process to use the API. An attacker could reach the user via email phishing,
pretending to be from Codex. The email might redirect to a malicious website or include a
form that, upon the user's click, triggers a request to the Codex node to create a new storage request.

```
   ──────
 ─│      ─│              ┌────────────────┐
│           │            │                │
│ Attacker  │───────────▶│ Email phishing │
│           │            │                │
 ─│      ─│              └────────────────┘
   ──────                        │
      •                          │
      •                          │
      •                          ▼
      •                       ──────
      •                     ─│      ─│
      •                    │           │
      •                    │   User    │
      •                    │           │
      •                     ─│      ─│
      •                       ──────
      •                          │
      •                          │
      •                          │  Clicks on the phishing email
      •                          │
      •                          │
      •                          ▼
      •                  ┌────────────────┐
      •                  │                │
      •                  │ Unsecure form  │
      •                  │                │
      •                  └────────────────┘
      •                          │
      •                          │  Submits the form
      •                          │
      •                          │  action=/storage/request/CIDMalicious method=POST
      •                          │  input name="pricePerBytePerSecond" value="100000"
      •                          ▼
      •                  ┌────────────────┐
      •                  │                │
      •                  │  Codex node    │
      •                  │                │
      •                  └────────────────┘
      •                          │
      •                          │   POST /storage/request/CIDMalicious
      •                          │   pricePerBytePerSecond: 1000000
      •                          │
      •                          ▼
      •                  ┌────────────────┐
      •                  │                │
      •••••••••••••••••••│ Contract done  │
                         │                │
                         └────────────────┘
```

Edit/view: https://cascii.app/437bc

#### Impacts

This could lead to two issues:

- **Financial Loss**: Malicious requests drain user wallet funds
- **Unwanted Content**: Attackers force storage of insecure or illegal files via
  malicious CIDs, risking legal or reputational harm.

#### Mitigation

Typically, such web phishing attacks are mitigated by authentication or a
[custom header](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#employing-custom-request-headers-for-ajaxapi) to verify the request’s legitimacy.

However, Codex does not have an authentication mechanism, making options like CSRF
tokens impractical and using a custom header would provide a poor user experience
in Codex, as users would need to set the header manually, which is cumbersome and error-prone.

Users can reduce the risk of significant fund drainage by employing a hot wallet with
a small amount of tokens designated for storage requests, while keeping the majority
of their funds in a cold wallet. This limits the exposure to phishing attacks, as only
the tokens in the hot wallet are at risk. For example, a user might allocate just enough
tokens to cover typical storage needs, minimizing potential losses.

While this strategy mitigates the financial impact of unwanted storage requests, it does
not address the storage of unwanted or illegal content. An attacker could still trick the
user into storing harmful files via phishing.

### Same-Chain attack replays

#### Scenario

An attacker reuses a user’s signed transaction on the same chain to spoof additional
requests, attempting to drain funds.

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

- **Financial Loss**: Duplicate requests drain user funds

#### Mitigation

Include a unique, random `nonce` in the request data. This ensures signatures are unique
per request, preventing reuse on the same chain. Codex’s current implementation includes
this, fully mitigating the threat.

### Cross-Chain attack replays

#### Scenario

An attacker captures a user’s signed transaction from one chain and replays it on another
with an identical `Marketplace.sol` contract. The signature, publicly visible in blockchain,
validates without needing the user’s private key, spoofing their intent.

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
           ▼                              ──────
┌──────────────────────┐                ─│      ─│
│                      │               │           │
│     Chain 1001       │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶│  Attacker │
│                      │               │           │
└──────────────────────┘                ─│      ─│
                                          ──────
```

Edit/view: https://cascii.app/9951e

#### Impacts

- **Financial Loss**: Replayed requests on another chain drain user funds

#### Mitigation

Implement EIP-712 to include chain-specific data in signed transaction, ensuring
signatures are valid only on the intended chain and preventing unauthorized replays
on other chains.

### Client spoofing via API

#### Scenario

A user starts a node locally and uses `api-bindaddr` with the value `0.0.0.0`.
Worse, he confuses port forwarding and enable it for the REST API as well.

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

- **Node full API control**: Attackers can send unauthorized API requests, draining funds
  or storing illegal content.

#### Mitigation

Educate the user to not use `0.0.0.0` for `api-bindaddr` unless he really knows what he
is doing and not enabling the port forwarding for the REST API. A warning during the
startup could be displayed if `api-bindaddr` is not bound to localhost.

## Tampering

Threat action aimed at altering stored files, proofs, or smart contracts to disrupt
the network.

### Fake proofs

#### Scenario

In the case of the proof verification is weak and proofs can be submitted and verified easily,
a storage provider could stop storing the data and attempts to send fake proofs, claiming they
are still hosting the content, using initial data received.

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
└────────────────────────┘              ╷
            ╷                           ╷
            ╷                           ╷
            ╷         Delete the file   ╷
            ╷         Submit fake proof ╷
            ╷                           ╷
            ╷                           ╷
            ╷                           ╷
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

Edit/view: https://cascii.app/9de0e

#### Impacts

- **Financial**: Attackers attempt to earn contract rewards at the end of the contract
  without storing the file.
- **Availability**: The slot becomes unavailable from that storage provider, reducing
  network reliability.

#### Mitigation

Codex issues periodic random challenges based on blockchain randomness to verify that
storage providers hold the data. Each failed challenge slashes the provider’s collateral.
After multiple failed proofs, the provider is removed from the contract, freeing the
slot for another provider.

### markProofAsMissing re-entrency

#### Scenario

A validator could exploit a reentrancy vulnerability in `markProofAsMissing` by re-entering
the function during an external token transfer, allowing multiple slashes and rewards
for a single missed proof within one transaction.

```js
// Generated from slither report
Reentrancy in Marketplace.markProofAsMissing(SlotId,Periods.Period) (contracts/Marketplace.sol#338-360):
        External calls:
        - assert(bool)(_token.transfer(msg.sender,validatorRewardAmount)) (contracts/Marketplace.sol#352)
        Event emitted after the call(s):
        - RequestFailed(requestId) (contracts/Marketplace.sol#396)
                - _forciblyFreeSlot(slotId) (contracts/Marketplace.sol#358)
        - SlotFreed(requestId,slot.slotIndex) (contracts/Marketplace.sol#385)
                - _forciblyFreeSlot(slotId) (contracts/Marketplace.sol#358)
```

```
                              ──────
                            ─│      ─│
                           │           │
                           │   User    │
                           │           │
                            ─│      ─│
                              ──────
                                 ╷
                        Storage  ╷
                        Request  ╷
                                 ▼
                   ┌───────────────────────────┐
Re-entrency        │                           │
                   │                           │
       ┌╶╶╶╶╶╶╶╶╶╶▶│      Codex network        │
       ╷           │                           │
       ╷           │                           │
       ╷           ▲───────────────────────────┘
       ╷           ╷             ╷
       ╷           ╷             ╷
    ──────         ╷             ╷                     ──────
  ─│      ─│       ╷             ╷                   ─│      ─│
 │           │     ╷             ╷                  │           │
 │ Validator │╶╶╶╶╶┘             ╷                  │    SP     │
 │           │                   ╷                  │           │
  ─│      ─│                     ╷                   ─│      ─│
    ──────                       ╷                     ──────
       ▲                         ╷                        ▲
       ╷                         ▼                        ╷
       ╷              ┌────────────────────┐              ╷
       └╶╶╶╶╶╶╶╶╶╶╶╶╶╶│Slot 1│Slot 2│Slot 3│╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
                      └────────────────────┘
```

Edit/view: https://cascii.app/0e182

#### Impacts

- **Financial**: Attackers could earn multiple validation rewards and excessively
  slash the host’s collateral for a single missed proof, draining funds unfairly.
- **Validation**: Repeated slashing disrupts PoR verification, potentially marking
  valid proofs as missing and undermining trust.

#### Mitigation

Apply the `Checks-Effects-Interactions` pattern by updating state before the external
`_token.transfer` call.
Use OpenZeppelin’s `ReentrancyGuard` to block reentrant calls.

[1]: https://owasp.org/www-community/Threat_Modeling_Process#stride
[2]: https://cdn2.hubspot.net/hubfs/4598121/Content%20PDFs/VerSprite-PASTA-Threat-Modeling-Process-for-Attack-Simulation-Threat-Analysis.pdf

## Repudiation

Threat action aimed at denying responsibility for uploading files or agreeing to storage
contracts in the network.

### Denial of file upload

#### Scenario

A user uploads illegal content to Codex and later denies initiating the request,
attempting to escape responsibility.

```
                  ──────
                ─│      ─│
               │           │
               │ Anonymous │
               │           │
                ─│      ─│
                  ──────
                     ╷
          Illegal    ╷
          Content    ╷
                     ▼
           ┌───────────────────┐
           │                   │
           │   Codex protocol  │
           │                   │
           └───────────────────┘
                     ▲
                     ╷
                     ╷
                     ╷
   ──────            ╷           ──────
 ─│      ─│          ╷         ─│      ─│
│           │        ╷        │           │
│   User    │╶╶╶╶╶╶╶╶└╶╶╶╶╶╶╶╶│   User    │
│           │                 │           │
 ─│      ─│      Download      ─│      ─│
   ──────                        ──────
```

Edit/view: https://cascii.app/5b9a9

#### Impacts

- **Reputation**: Codex could be used to distribute illegal content, leading to a
  loss of trust in the protocol.

#### Mitigation

Make a clear statement that Codex is not responsible for such content and warn users of the
potential risk for downloading an unknown CID.

### Clever host

#### Scenario

In this attack, an SP could fill a slot, and while fulfilling its duties, see
that a better opportunity has arisen, and abandon its duties in the first slot
to fill the second slot.

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
                   │  Clever host  │────────────────│Slot 1│Slot 2│Slot 3│
                   │               │                └────────────────────┘
                     │           │
                    ─│──      ───│
                        ──────
```

Edit/view: https://cascii.app/db2da

#### Impacts

- **Availability**: The slot becomes unavailable from that storage provider,
  reducing network reliability.

#### Mitigation

This attack is mitigated by the storage provider losing its request collateral for the first
slot once it is abandoned. Additionally, once the storage provider fills the first slot, it
will accrue rewards over time that will not be paid out until the request
successfully completes. These rewards act as another disincentive for the storage
provider to abandon the slot.

## Information disclosure

Information disclosure occurs when private or sensitive information such as user data,
file contents, or system secrets is unintentionally or maliciously revealed to unauthorized parties.

### Uploaded files exposed

#### Scenario

A user uploads a confidential file to Codex. Storage providers store non encrypted slots
of the file. Without encryption, storage providers could agree to gather slots and
reassemble the full content.

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
                           ╷                                   ╷
                           ╷                                   ╷
Fill Request 1 Slot 2      ╷                                   ╷
                           ▼                                   ╷
                        ──────       Abandon Request 1 Slot 2  ╷
                    ─│──      ───│   to fill Request 2 Slot 2  ╷
                     │           │                             ▼
                   │               │                ┌────────────────────┐
                   │  Clever host  │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶│Slot 1│Slot 2│Slot 3│
                   │               │                └────────────────────┘
                     │           │
                    ─│──      ───│
                        ──────
```

Edit/view: https://cascii.app/ef5ab

#### Impacts

- **Reputation**: Codex cannot guarantee confidentiality, leading to a loss of
  trust in the protocol.
- **Privacy**: Exposure of sensitive user data could violate privacy, potentially
  resulting in legal or regulatory consequences.

#### Mitigation

Implement encryption to ensure that only authorized users can decrypt and access the file contents.

## Denial of service

### Lazy host

#### Scenario

In the case of a single reservation system, matching storage providers are assigned to
slot reservation by a 1-1 relation, meaning that there is one storage provider
for one reservation.
A storage provider reserves a slot, but waits to fill the slot hoping a better
opportunity will arise, in which the reward earned in the new opportunity would be
greater than the reward earned in the original slot.

```
      ──────                                                ──────
    ─│      ─│                                            ─│      ─│
   │           │                                         │           │
   │   User    │                                         │   User    │
   │           │                                         │           │
    ─│      ─│                                            ─│      ─│
      ──────                                                ──────
         ╷                                                     ╷
         ╷                                                     ╷
         ╷                                                     ╷
         ╷                                                     ╷
         ╷                                                     ╷
         ╷               ┌────────────────────┐                ╷
         ╷               │                    │                ╷
         └╶╶╶╶╶╶╶╶╶╶╶╶╶╶▶│   Codex network    │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
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
             ╷                     ╷                       ╷
             ╷                     ╷                       ╷
             ╷                  ──────                     ╷
             ╷              ─│──      ───│                 ╷
             ╷               │           │                 ╷
             ╷             │               │               ╷
             └╶╶╶╶╶╶╶╶╶╶╶╶▶│   Lazy host   │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
                           │               │
Reserve Request 1 Slot 2     │           │      Reserve Request 2 Slot 2
                            ─│──      ───│
                                ──────
```

Edit/view: https://cascii.app/6144e

#### Impacts

- **Availability**: The storage request will fail because the storage provider assigned to the slot
  decided not to fill it for a better opportunity, leaving the slot empty.

#### Mitigation

This attack is mitigated by allowing for multiple reservations per slot.
All storage providers that have secured a reservation (capped at three) will race to fill the slot.
Thus, if one or more storage providers that have reserved the slot decide to
pursue other opportunities, the other storage providers that have reserved the slot will
still be able to fill the slot.

### Overload attack

#### Scenario

An attacker runs many small requests that generate high-volume transactions, overwhelming
validators and delaying their ability to detect missed proofs.

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
            ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷   │
            ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷  ╷   │
            ╷  ╷  └╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘  ╷   │
            ╷  ╷           ╷           ╷   │
            ╷  ╷           ▼           ╷   │
            ╷  └▶┌────────────────────◀┘   │
            ╷    │                    │    │
            └╶╶╶▶│       Codex        │◀───┘
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

Edit/view: https://cascii.app/b6a31

#### Impacts

- **System Disruption**: Hosts might temporarily avoid penalties for not serving content,
  reducing file availability and causing users to lose trust in the Codex protocol.

#### Mitigation

Codex requires a small fee for each request, which helps mitigate this threat.
Other mitigations are also possible: optimizing the validation process to make proof
checks faster, limiting the number of storage requests per IP, and setting a minimum
file upload size.

### Lazy Client

#### Scenario

A client may try to disrupt the network by making storage requests but never providing the
actual data to storage providers who are trying to fill the storage slots.

#### Impacts

- **Wasting Resources**: Storage providers waste their resources trying to store data that
  never gets provided, making the network less efficient.

#### Mitigation

The transaction cost for each request helps prevent this attack. The more requests the attacker
makes, the higher the cost will be because of rising gas fees and block fill rates.
This makes it expensive for attackers to keep sending fake requests and spamming the network.

### Censoring

#### Scenario

A Storage provider tries to block access to specific CIDsfrom the network in order to censor
certain content. This could also happen during a repair process when a service provider tries
to stop a freed slot from being repaired by not sharing the necessary data.

#### Impacts

- **Censored Content**: The service prodivder may stop users from accessing certain data,
  preventing them from retrieving content they need.
- **Data Unavailability**: If the service provider tries to block data during a repair,
  it could stop the network from restoring missing files, making the data unavailable.
- **Trust Issues**: Users may lose trust in the network if they believe that some service providers
  can block or censor content.

#### Mitigation

Even if one SP withholds certain content, the dataset and the blocked CID can be rebuilt using
chunks from other service providers. This means that the censored CID can still be accessed
through other nodes, making the attack less successful.

### Greedy

#### Scenario

A storage provider tries to fill multiple slots in a single request. This can be harmful because
it allows a single SP to control more resources than intended.

#### Impacts

- **Resource Control**: Reducing fairness and spreading resources not reparted.
- **Network Inefficiency**: Limit the opportunity for other SPs to participate, affecting the
  overall efficiency of the network.

#### Mitigation

The expanding window mechanism helps prevent this attack. It makes sure that no single SP can fill
all the slots in a request by gradually opening up space for other service providers.
This works most of the time, but it may not be fully effective once the request is about to expire.

### Sticky

#### Scenario

A storage provider tries to keep control of a storage slot during a contract renewal. The SP does
this by withholding the data from other SPs and waiting until the expanding window allows them to
fill the slot again. Since they already have the data, they can act faster than others and fill
the slot before anyone else.

#### Impacts

- **Unfair Advantage**: The service provider gains an unfair advantage by being able to renew the
  contract without giving other SPs a fair chance.
- **Network Centralization**: Llead to fewer service providers handling more data, making the network
  less balanced.

#### Mitigation

The attack is difficult and unlikely to work unless the service provider controls a large part of the
network. The expanding window mechanism also helps by spreading out control and giving other SPs a
fair chance to fill the slots.

## Elevation of privilege

Threat action intending to gain privileged access to resources in order to gain unauthorized access
to information or to compromise a system.

### Exploring a vulnerability

#### Scenario

An attacker finds a vulnerability in Codex’s smart contract after it’s deployed. Anyone can call it.
The attacker uses this to change deal terms in their favor, taking over the funds.

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
        ┌╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶▶│       Smart contracts     │
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

Edit/view: https://cascii.app/23869

#### Impacts

- **Financial Loss**: Attackers could tweak deals to steal funds or stop payments.
- **System Disruption**: The integrity of the Codex protocol is compromised, leading to a loss of trust.

#### Mitigation

Use upgradable contracts to allow for future fixes. Additionally, implement temporary admin roles
requiring multiple approvals for changing critical settings.
