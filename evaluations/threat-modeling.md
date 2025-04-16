# Threat Modeling

## Introduction

The goal of this threat modeling is to identify potential security vulnerabilities in the Codex protocol, enabling us to take actions to mitigate them. Additionally, it can serve as a starting point for directives in a security audit. The scope includes the [Nim codebase](https://github.com/codex-storage/nim-codex) and the [marketplace smart contracts](https://github.com/codex-storage/codex-contracts-eth).

## Methodology

The [STRIDE][1] framework is used due to its simplicity and the ability to quickly build an analysis.  
The [PASTA][2] framework was considered but is more business-oriented and suited for mature projects. Additionally, its process is heavier than STRIDE's.

Threat modeling is an iterative process, requiring constant updates as features are added or modified in the codebase. Documenting potential security vulnerabilities helps developers to keep them in mind during the code implementation.

Anyone is invited to contribute to this document, as it is a [collective effort](https://www.threatmodelingmanifesto.org) rather than a one-person task.

## Analysis

| Category    | Threat                           | Description                                                                                   | Impact                                                                      | Mitigation                                       |
| ----------- | -------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------ |
| Spoofing    | Phishing-Induced Spoofing        | Exploits the private key loaded directly into the app via phishing to send unwanted requests. | Draining the user's wallet funds, store unwanted content.                   | Use cold wallet.                                 |
| Spoofing    | Same-Chain Replay                | Reuses a signed transaction on the same chain to spoof user actions.                          | Drained wallet funds.                                                       | Include a unique nonce in request data.          |
| Spoofing    | Cross-Chain Replay               | Replays a signed transaction on another chain.                                                | Drained wallet funds.                                                       | Implement EIP-712.                               |
| Spoofing    | Client Spoofing via API          | Access to the exposed node to use the API.                                                    | Node full access.                                                           | Educate users.                                   |
| Tempering   | Fake proofs                      | The storage provider sends fake proofs.                                                       | Contracts reward without actual data storage, reducing network reliability. | Require random challenges periodically.          |
| Tempering   | `markProofAsMissing` re-entrancy | The validator uses re-entrancy to slash multiple times.                                       | Excessive collateral slashing of the host, proof validation failure.        | Apply the `Checks-Effects-Interactions` pattern. |
| Repudiation | Denial of File Upload            | User denies uploading illegal content.                                                        | Reputation impact and trust failure                                         | Make a clear legal statement.                    |
| Repudiation | Lazy Host                        | Service provider does not fill the slot’s content.                                            | Reduces network reliability.                                                | Allow multiple reservations per slot.            |

## Spoofing

Threat action aimed at impersonating users or storage providers to access or manipulate files and contracts in the network.

### Phishing-Induced Spoofing

#### Scenario

When starting a Codex node, the user must load his private key to pay for initiating new storage requests. This private key is loaded into memory, and there is no authentication process to use the REST API. An attacker could reach the user via email phishing, pretending to be from Codex. The email might redirect to a malicious website or include a form that, upon the user's click, triggers a request to the Codex node to create a new storage request.

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
- **Unwanted Content**: Attackers force storage of insecure or illegal files via malicious CIDs, risking legal or reputational harm.

#### Mitigation

Typically, such web phishing attacks are mitigated by authentication or a [custom header](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#employing-custom-request-headers-for-ajaxapi) to verify the request’s legitimacy.

However, Codex does not have an authentication mechanism, making options like CSRF tokens impractical and using a custom header would provide a poor user experience in Codex, as users would need to set the header manually, which is cumbersome and error-prone.

Users can reduce the risk of significant fund drainage by employing a hot wallet with a small amount of tokens designated for storage requests, while keeping the majority of their funds in a cold wallet. This limits the exposure to phishing attacks, as only the tokens in the hot wallet are at risk. For example, a user might allocate just enough tokens to cover typical storage needs, minimizing potential losses.

While this strategy mitigates the financial impact of unwanted storage requests, it does not address the storage of unwanted or illegal content. An attacker could still trick the user into storing harmful files via phishing.

### Same-Chain attack replays

#### Scenario

An attacker reuses a user’s signed transaction on the same chain to spoof additional requests, attempting to drain funds.

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
           │
           │
           │
           │    Storage request
           │
           │
           │
           ▼
┌──────────────────────┐
│                      │
│     Codex node       │
│                      │
└──────────────────────┘
           │
           │
           │
           ▼
┌──────────────────────┐
│                      │
│  Request signature   │••••••••••••••
│                      │             •
└──────────────────────┘             •
           │                         •
           │                      ──────
           │                    ─│      ─│
           │                   │           │
           │                   │ Attacker  │
           │                   │           │
           │                    ─│      ─│
           ▼                      ──────
┌──────────────────────┐             │
│                      │             │
│   Smart contract     │◀────────────┘
│                      │
└──────────────────────┘
```

Edit/view: https://cascii.app/3577b

#### Impacts

- **Financial Loss**: Duplicate requests drain user funds

#### Mitigation

Include a unique, random `nonce` in the request data. This ensures signatures are unique per request, preventing reuse on the same chain. Codex’s current implementation includes this, fully mitigating the threat.

### Cross-Chain Replay

#### Scenario

An attacker captures a user’s signed transaction from one chain and replays it on another with an identical `Marketplace.sol` contract. The signature, publicly visible in blockchain, validates without needing the user’s private key, spoofing their intent.

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
           │
           │
           │
           │    Storage request
           │
           │
           │
           ▼
┌──────────────────────┐
│                      │
│     Codex node       │
│                      │
└──────────────────────┘
           │
           │
           │
           ▼
┌──────────────────────┐
│                      │
│  Request signature   │
│                      │
└──────────────────────┘
           │
           │
           │
           │
           ▼
┌──────────────────────┐
│                      │
│   Smart contract     │                       ──────
│                      │                     ─│      ─│
└──────────────────────┘                    │           │
           │                      ••••••••••│ Attacker  │───────
           │                      •         │           │      │
           │                      •          ─│      ─│        │
           │                      •            ──────          │
           ▼                      •                            │
┌──────────────────────┐          •                            │       ┌──────────────────────┐
│                      │          •                            │       │                      │
│     Chain 1001       │•••••••••••                            └───────│      Chain 1002      │
│                      │                                               │                      │
└──────────────────────┘                                               └──────────────────────┘

```

Edit/view: https://cascii.app/d312b

#### Impacts

- **Financial Loss**: Replayed requests on another chain drain user funds

#### Mitigation

Implement EIP-712 to include chain-specific data in signed transaction, ensuring signatures are valid only on the intended chain and preventing unauthorized replays on other chains.

### Client Spoofing via API

#### Scenario

A user starts a node locally and uses `api-bindaddr` with the value `0.0.0.0`. Worse, he confuses port forwarding and enable it for the REST API as well.

```
                                                   ──────
                                               ─│──      ───│
                                                │           │
                                              │               │
                         ┌────────────────────│     User      │──────────────────┐
                         │                    │               │                  │
                         │                      │           │                    │
                         │                     ─│──      ───│                    │
                         │                         ──────                        │
                         │                                                       │
                         │ Starts with 0:0:0:0                                   │ Enables port forwarding for REST api
                         │                                                       │
                         │                                                       │
                         │                                                       │
                         │                                                       │
                         ▼                                                       ▼
              ┌──────────────────────┐                                ┌──────────────────────┐
              │                      │                                │                      │
              │      Codex node      │                                │      Codex node      │
              │                      │                                │                      │
              └──────────────────────┘                                └──────────────────────┘
                         ▲                                                       ▲
                         │                                                       │
                         │                                                       │
   ──────                │                                                       │                    ──────
 ─│      ─│              │                                                       │                  ─│      ─│
│ Attacker  │            │                                                       │                 │           │
│ on same   │────────────┘                                                       └─────────────────│ Attacker  │
│ network   │                                                                                      │           │
 ─│      ─│                                                                                         ─│      ─│
   ──────                                                                                             ──────
```

Edit/view: https://cascii.app/28692

#### Impacts

- **Node full control**: Attackers can send unauthorized API requests, draining funds or storing illegal content.

#### Mitigation

Educate the user to not use `0.0.0.0` for `api-bindaddr` unless he really knows what he is doing and not enabling the port forwarding for the REST API. A warning during the startup could be displayed if `api-bindaddr` is not bound to localhost.

## Tempering

Threat action aimed at altering stored files, proofs, or smart contracts to disrupt the network.

### Fake proofs

#### Scenario

After the Codex contract starts, a storage provider stops storing the data and attempts to send fake proofs, claiming they are still hosting the content, using initial data received.

```
         ──────
       ─│      ─│
      │           │
      │   User    │
      │           │
       ─│      ─│
         ──────
            │
  Storage   │
  Request   │
            │
            ▼
┌────────────────────────┐
│                        │
│      Codex network     │──────────────┐
│                        │              │
└────────────────────────┘              │
            │                           │
            │                           │
            │         Delete the file   │
            │         Submit fake proof │
            │                           │
            │                           │
            │                           │
            │                        ──────
            │                      ─│      ─│
            │                     │ Storage   │
            │                     │ Provider  │
            │                     │           │
            │                      ─│      ─│
            │                        ──────
            │                           ▲
            │                           •
            │                           •
            │                           •
            │                           •
            │                           •
            │                           •
            ▼                           •
 ┌────────────────────┐                 •
 │Slot 1│Slot 2│Slot 3│••••••••••••••••••
 └────────────────────┘
```

Edit/view: https://cascii.app/629b5

#### Impacts

- **Financial**: Attackers attempt to earn contract rewards at the end of the contract without storing the file.
- **Availability**: The file becomes unavailable from that storage provider, reducing network reliability.

#### Mitigation

Codex issues periodic random challenges based on blockchain randomness to verify that storage providers hold the data. Each failed challenge slashes the provider’s collateral. After multiple failed proofs, the provider is removed from the contract, freeing the slot for another provider.

### markProofAsMissing re-entrency

#### Scenario

A validator could exploit a reentrancy vulnerability in `markProofAsMissing` by re-entering the function during an external token transfer, allowing multiple slashes and rewards for a single missed proof within one transaction.

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
                                 │
                        Storage  │
                        Request  │
                                 ▼
                   ┌───────────────────────────┐
Re-entrency        │                           │
                   │                           │
       ┌╶╶╶╶╶╶╶╶╶╶▶│      Codex network        │
       ╷           │                           │
       ╷           │                           │
       ╷           ▲───────────────────────────┘
       ╷           ╷             │
       ╷           ╷             │
    ──────         ╷             │                     ──────
  ─│      ─│       ╷             │                   ─│      ─│
 │           │     ╷             │                  │           │
 │ Validator │╶╶╶╶╶┘             │                  │    SP     │
 │           │                   │                  │           │
  ─│      ─│                     │                   ─│      ─│
    ──────                       │                     ──────
       │                         │                        ▲
       │                         ▼                        •
       │              ┌────────────────────┐              •
       └──────────────│Slot 1│Slot 2│Slot 3│•••••••••••••••
                      └────────────────────┘
```

Edit/view: https://cascii.app/5ead7

#### Impacts

- **Financial**: Attackers could earn multiple validation rewards and excessively slash the host’s collateral for a single missed proof, draining funds unfairly.
- **Validation**: Repeated slashing disrupts PoR verification, potentially marking valid proofs as missing and undermining trust.

#### Mitigation

Apply the `Checks-Effects-Interactions` pattern by updating state before the external `_token.transfer` call.
Use OpenZeppelin’s `ReentrancyGuard` to block reentrant calls.

[1]: https://owasp.org/www-community/Threat_Modeling_Process#stride
[2]: https://cdn2.hubspot.net/hubfs/4598121/Content%20PDFs/VerSprite-PASTA-Threat-Modeling-Process-for-Attack-Simulation-Threat-Analysis.pdf

## Repudiation

Threat action aimed at denying responsibility for uploading files or agreeing to storage contracts in the network.

### Denial of file upload

#### Scenario

A user uploads illegal content to Codex and later denies initiating the request, attempting to evade responsibility.

```
                  ──────
                ─│      ─│
               │           │
               │ Anonymous │
               │           │
                ─│      ─│
                  ──────
                     │
          Illegal    │
          Content    │
                     ▼
           ┌───────────────────┐
           │                   │
           │   Codex protocol  │
           │                   │
           └───────────────────┘
                     ▲
                     │
                     │
                     │
   ──────            │           ──────
 ─│      ─│          │         ─│      ─│
│           │        │        │           │
│   User    │────────└────────│   User    │
│           │                 │           │
 ─│      ─│      Download      ─│      ─│
   ──────                        ──────
```

Edit/view: https://cascii.app/70aed

#### Impacts

- **Reputation**: Codex could be used to distribute illegal content, leading to a loss of trust in the protocol.

#### Mitigation

Make a clear statement that Codex is not responsible for such content and warn users of the potential risk for downloading an unknown CID.

### Lazy Host

#### Scenario

A storage provider reserves a slot, but waits to fill the slot hoping a better opportunity will arise, in which the reward earned in the new opportunity would be greater than the reward earned in the original slot.

```
      ──────                                                ──────
    ─│      ─│                                            ─│      ─│
   │           │                                         │           │
   │   User    │                                         │   User    │
   │           │                                         │           │
    ─│      ─│                                            ─│      ─│
      ──────                                                ──────
         │                                                     ╷
         │                                                     ╷
         │                                                     ╷
         │                                                     ╷
         │                                                     ╷
         │               ┌────────────────────┐                ╷
         │               │                    │                ╷
         └──────────────▶│   Codex network    │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
                         │                    │
             ┌───────────└────────────────────┘╶╶╶╶╶╶╶╶╶╶╶╶┐
             │                     ╷                       ╷
Request 1    │                     ╷                       ╷   Request 2
             │                     ╷                       ╷
             │                     ╷ Fill Request 2 Slot 2 ╷
             ▼                     ╷                       ▼
  ┌────────────────────┐           ╷            ┌────────────────────┐
  │Slot 1│Slot 2│Slot 3│           ╷            │Slot 1│Slot 2│Slot 3│
  └────────────────────┘           ╷            └────────────────────┘
             │                     ╷                       ╷
             │                     ╷                       ╷
             │                  ──────                     ╷
             │              ─│──      ───│                 ╷
             │               │           │                 ╷
             │             │               │               ╷
             └─────────────│   Lazy host   │◀╶╶╶╶╶╶╶╶╶╶╶╶╶╶┘
                           │               │
Reserve Request 1 Slot 2     │           │      Reserve Request 2 Slot 2
                            ─│──      ───│
                                ──────
```

Edit/view: https://cascii.app/69a55

#### Impacts

- **Availability**: The storage request will fail because the storage provider assigned to the slot decided not to fill it for a better opportunity, leaving the slot empty.

#### Mitigation

This attack is mitigated by allowing for multiple reservations per slot. All storage providers that have secured a reservation (capped at three) will race to fill the slot. Thus, if one or more storage providers that have reserved the slot decide to pursue other opportunities, the other storage providers that have reserved the slot will still be able to fill the slot.
