# Threat Modeling

## Introduction

The goal of this threat modeling is to identify potential security vulnerabilities in the Codex protocol, enabling us to take actions to mitigate them. Additionally, it can serve as a starting point for directives in a security audit. The scope includes the [Nim codebase](https://github.com/codex-storage/nim-codex) and the [marketplace smart contracts](https://github.com/codex-storage/codex-contracts-eth).

## Methodology

The [STRIDE][1] framework is used due to its simplicity and the ability to quickly build an analysis.  
The [PASTA][2] framework was considered but is more business-oriented and suited for mature projects. Additionally, its process is heavier than STRIDE's.

Threat modeling is an iterative process, requiring constant updates as features are added or modified in the codebase. Documenting potential security vulnerabilities helps developers to keep them in mind during the code implementation.

Anyone is invited to contribute to this document, as it is a [collective effort](https://www.threatmodelingmanifesto.org) rather than a one-person task.

## Analysis

| Category  | Threat                   | Description                                                                 | Impact                           | Mitigation                                                  |
|-----------|--------------------------|-----------------------------------------------------------------------------|----------------------------------|-------------------------------------------------------------|
| Spoofing  | Phishing-Induced Spoofing| Exploits the private key loaded directly into the app via phishing to send unwanted requests. | Draining the user's wallet funds, store unwanted content. | Use cold wallet. |
|           | Same-Chain Replay        | Reuses a signed request on the same chain to spoof user actions.            | Drained wallet funds.            | Include a unique nonce in request data.                     |
|           | Cross-Chain Replay       | Replays a signed request on another chain.          | Drained wallet funds.                    | Implement EIP-712.                                          |
|           | Client Spoofing via API  | Access to the exposed node to use the API.                                  | Node full access. | Educate users.
                            |
## Spoofing

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

An attacker reuses a user’s signed `StorageRequest` on the same chain to spoof additional requests, attempting to drain funds.

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
│  Request signature   │••••••••••••             
│                      │           •   ──────    
└──────────────────────┘           • ─│      ─│  
           │                       •│           │
           │                       •│ Attacker  │
           │                        │           │
           │                         ─│      ─│  
           ▼                           ──────    
┌──────────────────────┐                  │      
│                      │                  │      
│   Smart contract     │ ◀────────────────┘      
│                      │                         
└──────────────────────┘                         
```

Edit/view: https://cascii.app/8edc1                   


#### Impacts

- **Financial Loss**: Duplicate requests drain user funds

#### Mitigation

Include a unique, random `nonce` in the request data. This ensures signatures are unique per request, preventing reuse on the same chain. Codex’s current implementation includes this, fully mitigating the threat.

### Cross-Chain Replay

#### Scenario

An attacker captures a user’s signed `StorageRequest` from one chain and replays it on another with an identical `Marketplace.sol` contract. The signature, publicly visible in blockchain, validates without needing the user’s private key, spoofing their intent.

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
           │                      •                            │                               
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

Implement EIP-712 to include chain-specific data in signed storage requests, ensuring signatures are valid only on the intended chain and preventing unauthorized replays on other chains.

### Client Spoofing via API

#### Scenario

A user starts a node locally and uses `api-bindaddr` with the value `0.0.0.0`. Worse, he confuses port forwarding and enable it for the REST API as well.

```
                                                   ──────                                                                    
                                               ─│──      ───│                                                                
                                                │           │                                                                
                                              │               │                                                              
                                             ││     User      │──────────────────┐                                           
                                             ││               │                  │                                           
                                             │  │           │                    │                                           
                                             │ ─│──      ───│                    │                                           
                Starts with 0:0:0:0          │     ──────                        │       Enables port forwarding for REST api
                                             │                                   │                                           
                         ┌───────────────────┘                                   │                                           
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

Edit/view: https://cascii.app/1cca0

#### Impacts

- **Node full control**: Attackers can send unauthorized API requests, draining funds or storing illegal content.

#### Mitigation

Educate the user to not use `0.0.0.0` for `api-bindaddr` unless he really knows what he is doing and not enabling the port forwarding for the REST API. A warning during the startup could be displayed if `api-bindaddr` is not bound to localhost.

[1]: https://owasp.org/www-community/Threat_Modeling_Process#stride  
[2]: https://cdn2.hubspot.net/hubfs/4598121/Content%20PDFs/VerSprite-PASTA-Threat-Modeling-Process-for-Attack-Simulation-Threat-Analysis.pdf