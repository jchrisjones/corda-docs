---
aliases:
- /releases/4.4/index.html
- /docs/corda-enterprise/head/index.html
- /docs/corda-enterprise/index.html
date: '2020-01-08T09:59:25Z'
menu:
  versions:
    weight: -240
project: corda-enterprise
section_menu: corda-enterprise-4-4
title: Corda Enterprise 4.4
version: '4.4'
---

# Introduction to Corda

A Corda Network is a peer-to-peer network of [Nodes](node/component-topology.md), each representing a party on the network.
These Nodes run Corda applications [(CorDapps)](cordapps/cordapp-overview.md), and transact between Nodes using public or
confidential identities.

When one or more Nodes are involved in a transaction, the transaction must be notarised. [Notaries](notary/ha-notary-service-overview.md) are a specialized type
of Node that provides uniqueness consensus by attesting that, for a given transaction, it has not already signed other
transactions that consumes any of the proposed transaction’s input states.

For all Corda release notes, see the [Release Notes](release-notes-index.md) index page.

## Corda Enterprise

Corda Enterprise is a commercial edition of the Corda platform, specifically optimized to meet the privacy, security and
throughput demands of modern day business. Corda Enterprise is interoperable and compatible with Corda open source and
is designed for organizations with exacting requirements around quality of service and the network infrastructure in
which they operate.

Corda Enterprise contains all the core Corda functionality, but also includes the [Corda Firewall](node/corda-firewall-component.md),
support for high-availability Node and Notary deployments, and compatibility with hardware security modules [(HSMs)](node/operating/cryptoservice-configuration.md).

## Corda Enterprise vs Corda open source: feature comparison

More details on Corda Enterprise features compared to Corda open source features follow below.

### Corda Functionality

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|Corda ledger|&#9745;|&#9745;|
|Flow framework|&#9745;|&#9745;|
|Immutable states|&#9745;|&#9745;|
|Vault|&#9745;|&#9745;|
|Smart contracts|&#9745;|&#9745;|
|Atomic transactions (with input, output and reference states)|&#9745;|&#9745;|
|Multiple accounts|&#9745;|&#9745;|
|Supported development languages|Java, Kotlin|Java, Kotlin|
|Standard Corda APIs|&#9745;|&#9745;|
|Compatible with any Corda network (including the Corda Network)|&#9745;|&#9745;|

{{< /table >}}

### Node

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|Single node|&#9745;|&#9745;|
|Multiple nodes for high availability/disaster recovery|&#9746;|&#9745;|

{{< /table >}}

### Connectivity

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|In-process Artemis MQ|&#9745;|&#9745;|
|External Artemis MQ|&#9746;|&#9745;|
|Corda firewall|&#9746;|&#9745;|
|Multi-node use of a shared external Artemis MQ and a shared Corda firewall|&#9746;|&#9745;|

{{< /table >}}

### Key storage

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|Java keystore file|&#9745;|&#9745;|
|HSM support|&#9746;|&#9745;|

{{< /table >}}

### Vault databases

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|H2 (development use only)|&#9745;|&#9745;|
|Postgres|&#9745; Please note that this will be harmonised with Corda Enterprise in Corda 4.5 to allow for in-place upgrades|&#9745;|
|SQL Server|Experimental only|&#9745;|
|Oracle|&#9746;|&#9745;|

{{< /table >}}

### Notaries

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|Simple notary|&#9745;|&#9745;|
|Oracle RAC connectivity|&#9746;|&#9745;|
|CockroachDB connectivity|&#9746;|&#9745;|
|Clustered notary (for high availability)|&#9746;|&#9745;|

{{< /table >}}

### Performance

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|Dynamic database caching and performance enhancements|&#9746;|&#9745;|
|Multi-threaded flow state machine|&#9746;|&#9745;|

{{< /table >}}

### Tooling

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|Node health check tool|&#9746;|&#9745;|
|Configuration obfuscation tool|&#9746;|&#9745;|
|HA admin tool|&#9746;|&#9745;|

{{< /table >}}

### Support

{{< table >}}

|Feature|Corda open source|Corda Enterprise|
|------------------------------------------------------------|------------------------------|------------------------------|
|Developer mailing lists (no SLA)|&#9745;|&#9745;|
|Cordaledger slack (no SLA)|&#9745;|&#9745;|
|Software maintenance|&#9746;|&#9745;|
|Support by R3 Support Engineering|&#9746;|&#9745;|
|Access to R3 Professional Services|Upgrading to Corda Enterprise only |&#9745;|

{{< /table >}}
