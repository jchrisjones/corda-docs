---
aliases:
- /releases/4.3.1/corda-configuration-file.html
date: '2020-01-08T09:59:25Z'
menu:
  corda-enterprise-4-3-1:
    identifier: corda-enterprise-4-3-1-corda-configuration-file
    parent: corda-enterprise-4-3-1-corda-nodes-index
    weight: 1030
tags:
- corda
- configuration
- file
title: Node configuration
---


# Node configuration



## Configuration file location

When starting a node, the `corda.jar` file defaults to reading the node’s configuration from a `node.conf` file in the directory from which the command to launch Corda is executed.
There are two command-line options to override this behaviour:


* The `--config-file` command line option allows you to specify a configuration file with a different name, or in a different file location.
Paths are relative to the current working directory
* The `--base-directory` command line option allows you to specify the node’s workspace location.
A `node.conf` configuration file is then expected in the root of this workspace.

If you specify both command line arguments at the same time, the node will fail to start.


## Configuration file format

The Corda configuration file uses the HOCON format which is a superset of JSON. Please visit
[https://github.com/typesafehub/config/blob/master/HOCON.md](https://github.com/typesafehub/config/blob/master/HOCON.md) for further details.

Please do NOT use double quotes (`"`) in configuration keys.

Node setup will log `Config files should not contain " in property names. Please fix: [key]` as an error when it finds double quotes around keys.
This prevents configuration errors when mixing keys containing `.` wrapped with double quotes and without them e.g.: The property
`"dataSourceProperties.dataSourceClassName" = "val"` in [Reference.conf](#reference-conf) would be not overwritten by the property
`dataSourceProperties.dataSourceClassName = "val2"` in *node.conf*.


{{< warning >}}
If a property is defined twice the last one will take precedence. The library currently used for parsing HOCON
currently does not provide a way to catch duplicates when parsing files and will silently override values for the same key.
For example having `key=initialValue` defined first in node.conf and later on down the
lines `key=overridingValue` will result into the value being `overridingValue`.

{{< /warning >}}


By default the node will fail to start in presence of unknown property keys.
To alter this behaviour, the `on-unknown-config-keys` command-line argument can be set to `IGNORE` (default is `FAIL`).


## Overriding configuration values



### Placeholder Overrides

It is possible to add placeholders to the `node.conf` file to override particular settings via environment variables. In this case the
`rpcSettings.address` property will be overridden by the `RPC_ADDRESS` environment variable, and the node will fail to load if this
environment variable isn’t present (see: [Hiding sensitive data](node-administration.md#hiding-sensitive-data) for more information).

```groovy
rpcSettings {
  address=${RPC_ADDRESS}
  adminAddress="localhost:10015"
}
```


### Direct Overrides

It is also possible to directly override Corda configuration (regardless of whether the setting is already in the `node.conf`), by using
environment variables or JVM options. Simply prefix the field with `corda.` or `corda_`, using periods (`.`) or
underscores (`_`) to signify nested options. For example, to override the `rpcSettings.address` setting, you can override it via environment variables:

```shell
# For *nix systems:
export corda_rpcSettings_address=localhost:10015

# On Windows systems:
SET corda_rpcSettings_address=localhost:10015
SET corda.rpcSettings.address=localhost:10015
```

Or via JVM arguments:

```shell
java -Dcorda_rpcSettings_address=localhost:10015 -jar corda.jar
java -Dcorda.rpcSettings.address=localhost:10015 -jar corda.jar
```

Items in lists can be overridden by appending the list index to the configuration key. For example, the `jarDirs` setting can be
overridden via:

```shell
# via JVM arguments:
java -Dcorda.jarDirs.0=./libs -Dcorda.jarDirs.1=./morelibs -jar corda.jar
java -Dcorda_jarDirs_0=./libs -Dcorda_jarDirs_1=./morelibs -jar corda.jar

# or via environment variables

# for *nix systems:
export corda_jarDirs_0=./libs
export corda_jarDirs_1=./morelibs

# for Windows systems:
SET corda.jarDirs.0=./libs
SET corda.jarDirs.1=./morelibs
# or
SET corda_jarDirs_0=./libs
SET corda_jarDirs_1=./morelibs
```


#### Limitations


* If the same key is overridden by both an environment variable and system property, the system property takes precedence.
* Variables and properties are case sensitive. Corda will warn you if a variable
prefixed with `CORDA` cannot be mapped to a valid property. Shadowing occurs when two properties
of the same type with the same key are defined. For example having `corda.p2Aaddress=host:port` and `corda_p2Aaddress=host1:port1`
will raise an exception on startup. This is to prevent hard to spot mistakes.
* If an item in a list is overridden via an environment variable/system property, the whole list will be overridden. E.g., with a `node.conf`
containing:

```groovy
jarDirs=["./dir1", "./dir2", "./dir3"]
```

When Corda is started via:

```shell
java -Dcorda.jarDirs_0=./newdir1
```

The resulting value of `jarDirs` will be `["./newdir1"]`.
* You can’t override a populated list with an empty list. For example, when `devMode=false`, `cordappSignerKeyFingerprintBlacklist` is
pre-populated with Corda development keys. It isn’t possible to set this to an empty list via the commandline. You can however override
the list with an all zero hash which will remove the keys:

```shell
java -Dcorda.cordappSignerKeyFingerprintBlacklist.0="0000000000000000000000000000000000000000000000000000000000000000"
```


* Objects in lists cannot currently be overridden. For example the `rpcUsers` configuration key is a list of user objects, overriding these
via environment variables or system properties will not work.


## Configuration file fields

{{< note >}}
The available configuration fields are listed below in alphabetic order.

{{< /note >}}

An array of additional host:port values, which will be included in the advertised NodeInfo in the network map in addition to the [p2pAddress](#corda-configuration-file-p2paddress).
Nodes can use this configuration option to advertise HA endpoints and aliases to external parties.*Default:* empty listOptionally specify how much memory should be used to cache attachment contents in memory.*Default:* 10MBOptionally specify how many attachments should be cached locally. Note that this includes only the key and metadata, the content is cached separately and can be loaded lazily.*Default:* 1024
List of SHA-256 hashes of public keys. Attachments signed by any of these public keys will not be considered as trust roots for any attachments received over the network.
This property is similar to [cordappSignerKeyFingerprintBlacklist](#corda-configuration-file-signer-blacklist) but only restricts CorDapps that were
included as attachments in a transaction and received over the network from a peer.See [Signing CorDapps for use with Signature Constraints](api-contract-constraints.md#signing-cordapps-for-use-with-signature-constraints) for more information about signing CorDapps and what
makes an attachment trusted (a trust root).This property requires retrieving the hashes of public keys that need to be blacklisted. More information on this process can be found in [Generating a public key hash](#generating-a-public-key-hash).> 
*Default:* not defined
The root address of the Corda compatibility zone network management services, it is used by the Corda node to register with the network and obtain a Corda node certificate, (See [Network certificates](permissioning.md) for more information.) and also is used by the node to obtain network map information.
Cannot be set at the same time as the [networkServices](#corda-configuration-file-networkservices) option.**Important:  old configuration value, please use networkServices***Default:* not defined
List of the public keys fingerprints (SHA-256 of public key hash) not allowed as Cordapp JARs signers.
The node will not load Cordapps signed by those keys.
The option takes effect only in production mode and defaults to Corda development keys (`["56CA54E803CB87C8472EBD3FBC6A2F1876E814CEEBF74860BD46997F40729367", "83088052AF16700457AE2C978A7D8AC38DD6A7C713539D00B897CD03A5E5D31D"]`), in development mode any key is allowed to sign Cordpapp JARs.This property requires retrieving the hashes of public keys that need to be blacklisted. More information on this process can be found in [Generating a public key hash](#generating-a-public-key-hash).*Default:* not definedThis is a boolean flag that when enabled (i.e. `true` value is set) causes certificate revocation list (CRL) checking to use soft fail mode.
Soft fail mode allows the revocation check to succeed if the revocation status cannot be determined because of a network error.
If this parameter is set to `false` rigorous CRL checking takes place. This involves each certificate in the certificate path being checked for a CRL distribution point extension, and that this extension points to a URL serving a valid CRL.
This means that if any CRL URL in the certificate path is inaccessible, the connection with the other party will fail and be marked as bad.
Additionally, if any certificate in the hierarchy, including the self-generated node SSL certificate, is missing a valid CRL URL, then the certificate path will be marked as invalid.*Default:* trueOptional name of the CryptoService implementation. This only needs to be set if you intend to use a different provider than the default one
(see [HSM support for legal identity keys](cryptoservice-configuration.md)).Optional path to the configuration file for the CryptoService provider. This may have to be present if you use a different CryptoService provider
than the default one (see [HSM support for legal identity keys](cryptoservice-configuration.md)).Optional timeout value of actions sent to the the CryptoService (HSM). If the HSM takes longer than this duration to respond then a `TimedCryptoServiceException` will be thrown and handled by the Flow Hospital.*Default:* 1sSet custom command line attributes (e.g. Java system properties) on the node process via the capsule launcherA list of JVM arguments to apply to the node process. This removes any defaults specified from `corda.jar`, but can be overridden from the command line.
See [Setting JVM arguments](running-a-node.md#setting-jvm-args) for examples and details on the precedence of the different approaches to settings arguments.*Default:* not defined
Database configurationTransaction isolation level as defined by the `TRANSACTION_` constants in `java.sql.Connection`, but without the `TRANSACTION_` prefix.*Default:* `REPEATABLE_READ`Whether to export Hibernate JMX statistics.**Caution: enabling this option causes expensive run-time overhead***Default:* falseThe property is used only when a node runs against a H2 database, and it’s replaced by the `runMigration` property for other databases.
Boolean which indicates whether to update the database schema at startup (or create the schema when node starts for the first time).
If set to `false` on startup, the node will validate if it’s running against a compatible database schema.*Default:* trueThe property is used only when a node runs against a H2 database.
The property allows to override `database.initialiseSchema` for the Hibernate DDL generation for CorDapp schemas.
`UPDATE` performs an update of CorDapp schemas, while `VALID` only verifies their integrity and `NONE` performs no check.
When `initialiseSchema` is set to `false`, then `initialiseAppSchema` may be set as `VALID` or `NONE` only.*Default:* CorDapp schema creation is controlled with `initialiseSchema`.Boolean on whether to run the database migration scripts at startup. In production please keep it false. For more information please
check [Database management scripts](database-management.md). If migration is not run, on startup, the node will check if it’s running on the correct database version.
The property is used only when a node runs against a database other than H2, and it’s replaced by the `initialiseSchema` property for other databases.*Default:* falseSome database providers require a schema name when generating DDL and SQL statements. The value is passed to the Hibernate
property ‘hibernate.default_schema’. This is optional.Optional property for testing/development against an unsupported database. The value is passed to Hibernate `hibernate.dialect` option.
All supported databases don’t require this option, as Hibernate sets the correct dialect value out of box.This section is used to configure the JDBC connection and database driver used for the node’s persistence.
Node database contains example configurations for other database providers.
To add additional data source properties (for a specific JDBC driver) use the `dataSource.` prefix with the property name (e.g. `dataSource.customProperty = value`).JDBC Data Source class name.JDBC database URL.Database user.Database password.*Default:*

```none
dataSourceClassName = org.h2.jdbcx.JdbcDataSource
dataSource.url = "jdbc:h2:file:"${baseDirectory}"/persistence;DB_CLOSE_ON_EXIT=FALSE;WRITE_DELAY=0;LOCK_TIMEOUT=10000"
dataSource.user = sa
dataSource.password = ""
```

This flag toggles the auto IP detection behaviour.
If enabled, on startup the node will attempt to discover its externally visible IP address first by looking for any public addresses on its network interfaces, and then by sending an IP discovery request to the network map service.
Set to `true` to enable.*Default:* false
This flag sets the node to run in development mode.
On startup, if the keystore `<workspace>/certificates/sslkeystore.jks`
does not exist, a developer keystore will be used if `devMode` is true.
The node will exit if `devMode` is false and the keystore does not exist.
`devMode` also turns on background checking of flow checkpoints to shake out any bugs in the checkpointing process.
Also, if `devMode` is true, Hibernate will try to automatically create the schema required by Corda or update an existing schema in the SQL database; if `devMode` is false, Hibernate will simply validate the existing schema, failing on node start if the schema is either not present or not compatible.
If no value is specified in the node configuration file, the node will attempt to detect if it’s running on a developer machine and set `devMode=true` in that case.
This value can be overridden from the command line using the `--dev-mode` option.This flag affects the default value for Java heap size. See [Memory usage and tuning](node-administration.md#memory-usage-and-tuning) for further details.*Default:* Corda will try to establish based on OS environmentAllows modification of certain `devMode` features**Important: This is an unsupported configuration.**Allows a node configured to operate in development mode to connect to a compatibility zone.*Default:* not definedThe email address responsible for node administration, used by the Compatibility Zone administrator.*Default:* [company@example.com](mailto:company@example.com)Allows fine-grained controls of various features only available in the enterprise version of Corda.

Enable the protective heartbeat logic so that only one node instance is ever running (hot-cold deployment).Enables the logic. Values can be either true or false.*Default:* falseInterval in milliseconds used by the node to update the lock on the database.*Default:* not definedInterval in milliseconds used by the node to try and acquire the lock on the database.*Default:* not definedEnables the health check feature required by the [Health Survey Tool](health-survey.md#health-survey-ref).*Default:* trueEnables P2P communication to pass through the Corda Firewall.*Default:* falseThe alias of the identity key. Allowed are up to 100 lower case alphanumeric characters and the hyphen (-).*Default:* identity-private-keyThe alias of the CA key. Allowed are up to 100 lower case alphanumeric characters and the hyphen (-).*Default:* cordaclientcaThe alias of the distributed notary signing key alias (used if this node is a notary). Allowed are up to 100 lower case alphanumeric
characters and the hyphen (-).*Default:* distributed-notary-private-keymessagingServerSslConfiguration


The path to the KeyStore file to use in Artemis connections.*Default:* not definedThe password for the TLS KeyStore.*Default:* not definedThe path to the TrustStore file to use in Artemis connections.*Default:* not definedThe password for TLS TrustStore.*Default:* not defined
Mode used when setting up the Artemis client. Supported modes are: DEFAULT (5 initial connect attempts, 5 reconnect attempts in case of failure, starting retry interval of 5 seconds with an exponential back-off multiplier of 1.5 for up to 3 minutes retry interval),
FAIL_FAST (no initial attempts, no reconnect attempts), CONTINUOUS_RETRY (infinite initial and reconnect attempts, starting retry interval of 5 seconds with an exponential back-of multiplier of 1.5 up for up to 5 minutes retry interval).*Default:* DEFAULTList of Artemis Server back-up addresses. If any back-ups are specified, the client will be configured to automatically failover to the first server it can connect to.*Default:* empty listThis is an optional crypto service configuration which will be used for HSM TLS signing when interacting with the Artemis message server.
This option only makes sense when running a standalone Artemis messaging server to connect to the Bridge.
If this option is missing, the local file system will be used to store private keys inside `JKS` key stores.> 
The name of HSM provider to be used. E.g.: `UTIMACO`, `GEMALTO_LUNA`, etc. Please see: [Crypto service configuration](cryptoservice-configuration.md).Absolute path to HSM provider specific configuration which will contain everything necessary to establish connection with HSM.
*Default* Not present so local file system is used.


Performance tuning parameters for Corda EnterpriseThe number of threads available to handle flows in parallel. This is the number of flows
that can run in parallel doing something and/or holding resources like database connections.
A larger number of flows can be suspended, e.g. waiting for reply from a counterparty.
When a response arrives, a suspended flow will be woken up if there are any available threads in the thread pool.
Otherwise, a currently active flow must be finished or suspended before the suspended flow can be woken
up to handle the event. This can have serious performance implications if the flow thread pool is too small,
as a flow cannot be suspended while in a database transaction, or without checkpointing its state first.
Corda Enterprise allows the node operators to configure the number of threads the state machine manager can use to execute flows in
parallel, allowing more than one flow to be active and/or use resources at the same time.The default value is 2 times the number of cores available (the minimum is 30 if there are less than 15 cores) which was found to be
working efficiently in performance testing.
The ideal value for this parameter depends on a number of factors.
The main ones are the hardware the node is running on, the performance profile of the
flows, and the database instance backing the node as datastore. Every thread will open a database connection,
so for n threads, the database system must have at least n+1 connections available. Also, the database
must be able to actually cope with the level of parallelism to make the number of threads worthwhile - if
using e.g. H2, any number beyond 8 does not add any substantial benefit due to limitations with its internal
architecture. For these reasons, the default size for the flow framework thread pool is the minimum between two times the available number of processors and 30. Overriding this value in the configuration allows to specify any number.The number of threads handling RPC calls - this defines how many RPC requests can be handled
in parallel without queueing. The default value is set to the number of available processor cores.
Incoming RPC calls are queued until a thread from this
pool is available to handle the connection, prepare any required data and start the requested flow. As this
might be a non-trivial amount of work, the size of this pool can be configured in Corda Enterprise.
On a multicore machine with a large `flowThreadPoolSize`, this might need to be increased, to avoid flow
threads being idle while the payload is being deserialized and the flow invocation run.If there are idling flow threads while RPC calls are queued, it might be worthwhile increasing this number slightly.
Valid values for this property are between 4 (that is the number used for the single threaded state machine in
open source) and the number of flow threads.
An optional list of private network map UUIDs. Your node will fetch the public network and private network maps based on these keys.
Private network UUID should be provided by network operator and lets you see nodes not visible on public network.**Important: This is a temporary feature for onboarding network participants that limits their visibility for privacy reasons.***Default:* not definedDuration of the period suspended flows waiting for IO are logged.*Default:* 60 secondsThreshold duration suspended flows waiting for IO need to exceed before they are logged.*Default:* 60 secondsWhen a flow implementing the `TimedFlow` interface and setting the `isTimeoutEnabled` flag does not complete within a defined elapsed time, it is restarted from the initial checkpoint.
Currently only used for notarisation requests with clustered notaries: if a notary cluster member dies while processing a notarisation request, the client flow eventually times out and gets restarted.
On restart the request is resent to a different notary cluster member in a round-robin fashion. Note that the flow will keep retrying forever.The initial flow timeout period.*Default:* 30 secondsThe number of retries the back-off time keeps growing for.
For subsequent retries, the timeout value will remain constant.*Default:* 6The base of the exponential backoff, *t_{wait} = timeout * backoffBase^{retryCount}**Default:* 1.8Optionally export metrics to a Graphite server. When specified, the node will push out all JMX metrics to the specified Graphite server at regular intervals.Server name or IP address of the Graphite instance.Port the Graphite instance is listening at.Optional prefix string to identify metrics from this node, will default to a string made up from Organisation Name and IP address.Optional wait time between pushing metrics. This will default to 60 seconds.Defines port for h2 DB.**Important: Deprecated please use h2Setting instead**
Sets the H2 JDBC server host and port.
See [Database access when running H2](node-database-access-h2.md).
For non-localhost address the database password needs to be set in `dataSourceProperties`.*Default:* NULL
An optional list of file system directories containing JARs to include in the classpath when launching via `corda.jar` only.
Each should be a string.
Only the JARs in the directories are added, not the directories themselves.
This is useful for including JDBC drivers and the like. e.g. `jarDirs = [ ${baseDirectory}"/libs" ]`.
(Note that you have to use the `baseDirectory` substitution value when pointing to a relative path).*Default:* not defined{{< note >}}
This property is only available for Corda distributed with Capsule. For the Corda tarball distribution this option is unavailable.
It’s advisable to copy any required JAR files to the ‘drivers’ subdirectory of the node base directory.{{< /note >}}
If set, will enable JMX metrics reporting via the Jolokia HTTP/JSON agent on the corresponding port.
Default Jolokia access url is [http://127.0.0.1:port/jolokia/](http://127.0.0.1:port/jolokia/)*Default:* not definedProvides an option for registering an alternative JMX reporter.
Available options are `JOLOKIA` and `NEW_RELIC`.The Jolokia configuration is provided by default.
The New Relic configuration leverages the [Dropwizard](https://metrics.dropwizard.io/3.2.3/manual/third-party.html) NewRelicReporter solution.
See [Introduction to New Relic for Java](https://docs.newrelic.com/docs/agents/java-agent/getting-started/introduction-new-relic-java) for details on how to get started and how to install the New Relic Java agent.*Default:* `JOLOKIA`

The password to unlock the KeyStore file (`<workspace>/certificates/sslkeystore.jks`) containing the node certificate and private key.**Important: This is the non-secret value for the development certificates automatically generated during the first node run.
Longer term these keys will be managed in secure hardware devices.***Default:* cordacadevpassInternal option.**Important: Please do not change.***Default:* trueThe address of the ArtemisMQ broker instance.
If not provided the node will run one locally.*Default:* not definedIf `messagingServerAddress` is specified the default assumption is that the artemis broker is running externally.
Setting this to `false` overrides this behaviour and runs the artemis internally to the node, but bound to the address specified in `messagingServerAddress`.
This allows the address and port advertised in `p2pAddress` to differ from the local binding, especially if there is external remapping by firewalls, load balancers , or routing rules. Note that `detectPublicIp` should be set to `false` to ensure that no translation of the `p2pAddress` occurs before it is sent to the network map.*Default:* not defined
The legal identity of the node.
This acts as a human-readable alias to the node’s public key and can be used with the network map to look up the node’s info.
This is the name that is used in the node’s certificates (either when requesting them from the doorman, or when auto-generating them in dev mode).
At runtime, Corda checks whether this name matches the name in the node’s certificates.
For more details please read [Node identity](node-naming.md#node-naming) chapter.*Default:* not defined
Optional configuration object which if present configures the node to run as a notary. If running as part of a HA notary cluster, please
specify the `serviceLegalName` and either the `mysql` (deprecated) or `jpa` configuration as described below. For a single-node notary only the `validating` property is required.Boolean to determine whether the notary is a validating or non-validating one.*Default:* falseIf the node is part of a distributed cluster, specify the legal name of the cluster.
At runtime, Corda checks whether this name matches the name of the certificate of the notary cluster.*Default:* not definedIf using the MySQL notary (deprecated), specify this configuration section with the settings below. For more details refer to [Configuring the notary worker nodes](running-a-notary-cluster/installing-the-notary-service.md).> 
The number of times to retry connection to the MySQL database. This should be based on the number of database servers in the replicated
setup.*Default:* 2, for a 3 server cluster.This section is used to configure the JDBC connection to the database cluster. For example:JDBC operation mode where every update to the database is immediately made permanent. For HA notary it has to be disabled, i.e. set to `"false"`.*Default:* not definedThe JDBC connection string. Has to contain a comma-separated list of IPs for all database servers. For example, if we have a 3-node Percona cluster with addresses 10.18.1.1, 10.18.1.2 and 10.18.1.3,
and the database name is `corda`:

```kotlin
"[jdbc:mysql://10.18.1.1,10.18.1.2,10.18.1.3/corda?rewriteBatchedStatements=true&useSSL=false&failOverReadOnly=false](jdbc:mysql://10.18.1.1,10.18.1.2,10.18.1.3/corda?rewriteBatchedStatements=true&useSSL=false&failOverReadOnly=false.md)"
```


*Default:* not definedDatabase user.*Default:* not definedDatabase password.*Default:* not defined
Example configuration:

```kotlin
mysql {
  connectionRetries=2
  dataSource {
    autoCommit="false"
    jdbcUrl="[jdbc:mysql://10.18.1.1,10.18.1.2,10.18.1.3/corda?rewriteBatchedStatements=true&useSSL=false&failOverReadOnly=false](jdbc:mysql://10.18.1.1,10.18.1.2,10.18.1.3/corda?rewriteBatchedStatements=true&useSSL=false&failOverReadOnly=false.md)"
    username="CordaUser"
    password="myStrongPassword"
  }
}
```

*(Deprecated)* If part of a distributed Raft cluster, specify this configuration object with the following settings:> 
The host and port to which to bind the embedded Raft server. Note that the Raft cluster uses a
separate transport layer for communication that does not integrate with ArtemisMQ messaging services.*Default:* not definedMust list the addresses of all the members in the cluster. At least one of the members must
be active and be able to communicate with the cluster leader for the node to join the cluster. If empty, a
new cluster will be bootstrapped.*Default:* not defined
*(Deprecated)* If part of a distributed BFT-SMaRt cluster, specify this configuration object with the following settings:> 
The zero-based index of the current replica. All replicas must specify a unique replica id.*Default:* not definedMust list the addresses of all the members in the cluster. At least one of the members must
be active and be able to communicate with the cluster leader for the node to join the cluster. If empty, a
new cluster will be bootstrapped.*Default:* not defined
If using the JPA notary, specify this configuration section with the settings below. For more details refer to [Configuring the notary worker nodes](running-a-notary-cluster/installing-the-notary-service.md).> 
The number of times to retry connection to the database. This should be based on the number of database servers in the replicated
setup.Boolean which indicates whether to update the database schema at startup (or create the schema when notary starts for the first time).
This property is used only when a notary runs against an H2 database. For information on schema setup for non H2 databases, please
see [Configuring the notary backend - JPA](running-a-notary-cluster/installing-jpa.md).*Default:* trueSets whether to validate the database schema before allowing the notary to start. Will prevent the notary from starting if validation fails with log messages indicating the reason(s)
for the failure. The validation will ensure that the database tables match that of the entities configured in the notary. This will not check whether any migrations have been run.*Default:* falseSets the schema to be used by HibernateOptionally sets the Hibernate dialect to use when communicating with the database.This section is used to configure the JDBC connection to the database cluster. For example:JDBC operation mode where every update to the database is immediately made permanent. For HA notary it has to be disabled, i.e. set to `"false"`.*Default:* not definedThe JDBC connection string. Has to contain a comma-separated list of IPs for all database servers. For example, if we have a 3-node CockroachDB cluster with addresses 10.18.1.1, 10.18.1.2 and 10.18.1.3,
and the notary worker is connecting to CockroachDB via SSL using certificates created for the user `corda`:

```kotlin
"[jdbc:postgresql://10.18.1.1,10.18.1.2,10.18.1.3/corda?sslmode=require&sslrootcert=certificates/ca.crt&sslcert=certificates/client.corda.crt&sslkey=certificates/client.corda.key.pk8](jdbc:postgresql://10.18.1.1,10.18.1.2,10.18.1.3/corda?sslmode=require&sslrootcert=certificates/ca.crt&sslcert=certificates/client.corda.crt&sslkey=certificates/client.corda.key.pk8)"
```


*Default:* not definedDatabase user.*Default:* not definedDatabase password.*Default:* not defined
Example configuration:

```kotlin
jpa {
  connectionRetries=2
  dataSource {
    autoCommit="false"
    jdbcUrl="[jdbc:postgresql://10.18.1.1,10.18.1.2,10.18.1.3/corda?sslmode=require&sslrootcert=certificates/ca.crt&sslcert=certificates/client.corda.crt&sslkey=certificates/client.corda.key.pk8&user=corda](jdbc:postgresql://10.18.1.1,10.18.1.2,10.18.1.3/corda?sslmode=require&sslrootcert=certificates/ca.crt&sslcert=certificates/client.corda.crt&sslkey=certificates/client.corda.key.pk8&user=corda)"
    username="corda"
    password="myStrongPassword"
  }
}
```

Optional settings for managing the network parameter auto-acceptance behaviour.
If not provided then the defined defaults below are used.This flag toggles auto accepting of network parameter changes.
If a network operator issues a network parameter change which modifies only auto-acceptable options and this behaviour is enabled then the changes will be accepted without any manual intervention from the node operator.
See [The network map](network-map.md) for more information on the update process and current auto-acceptable parameters.
Set to `false` to disable.*Default:* trueList of auto-acceptable parameter names to explicitly exclude from auto-accepting.
Allows a node operator to control the behaviour at a more granular level.*Default:* empty list
If the Corda compatibility zone services, both network map and registration (doorman), are not running on the same endpoint
and thus have different URLs then this option should be used in place of the `compatibilityZoneURL` setting.**Important: Only one of ``compatibilityZoneURL`` or ``networkServices`` should be used.**Root address of the network registration service.*Default:* not definedRoot address of the network map service.*Default:* not definedOptional UUID of the private network operating within the compatibility zone this node should be joining.*Default:* not definedOptional - this can be used to turn on using a proxy for the http connections to doorman and network map. Allowed
values are `DIRECT`, `HTTP` and `SOCKS`. If set to anything else than `DIRECT`, the proxyAddress must also
be set.*Default:* `DIRECT` (i.e. no proxy)Optional hostname and port of a HTTP or SOCKS proxy to be used for connections to the network map or doorman.*Default:* not definedOptional user name for authentication with the proxy. Note that Corda only supports username/password based
basic authentication.Optional password for authentication with the proxy. The password can be obfuscated using the [Configuration Obfuscator](tools-config-obfuscator.md).
The host and port on which the node is available for protocol operations over ArtemisMQ.In practice the ArtemisMQ messaging services bind to **all local addresses** on the specified port.
However, note that the host is the included as the advertised entry in the network map.
As a result the value listed here must be **externally accessible when running nodes across a cluster of machines.**
If the provided host is unreachable, the node will try to auto-discover its public one.*Default:* not definedIf provided, the node will attempt to tunnel inbound connections via an external relay. The relay’s address will be
advertised to the network map service instead of the provided `p2pAddress`.Hostname of the relay machineA port on the relay machine that accepts incoming TCP connections. Traffic will be forwarded from this port to the local port specified in `p2pAddress`.Username for establishing an SSH connection with the relay.Path to the private key file for SSH authentication. The private key must not have a passphrase.Path to the public key file for SSH authentication.Port to be used for SSH connection, default `22`.The address of the RPC system on which RPC requests can be made to the node.
If not provided then the node will run without RPC.**Important: Deprecated. Use rpcSettings instead.***Default:* not defined
Options for the RPC server exposed by the Node.**Important: The RPC SSL certificate is used by RPC clients to authenticate the connection.  The Node operator must provide RPC clients with a truststore containing the certificate they can trust.  We advise Node operators to not use the P2P keystore for RPC.  The node can be run with the “generate-rpc-ssl-settings” command, which generates a secure keystore and truststore that can be used to secure the RPC connection. You can use this if you have no special requirements.**> 
host and port for the RPC server binding.*Default:* not definedhost and port for the RPC admin binding (this is the endpoint that the node process will connect to).*Default:* not definedboolean, indicates whether the node will connect to a standalone broker for RPC.*Default:* falseboolean, indicates whether or not the node should require clients to use SSL for RPC connections.*Default:* false(mandatory if `useSsl=true`) SSL settings for the RPC server.Absolute path to the key store containing the RPC SSL certificate.*Default:* not definedPassword for the key store.*Default:* not defined

A list of users who are authorised to access the RPC system.
Each user in the list is a configuration object with the following fields:Username consisting only of word characters (a-z, A-Z, 0-9 and _)*Default:* not definedThe password*Default:* not definedA list of permissions for starting flows via RPC.
To give the user the permission to start the flow `foo.bar.FlowClass`, add the string `StartFlow.foo.bar.FlowClass` to the list.
If the list contains the string `ALL`, the user can start any flow via RPC. Wildcards are also allowed, for example `StartFlow.foo.bar.*`
will allow the user to start any flow within the `foo.bar` package.
This value is intended for administrator users and for development.*Default:* not definedContains various nested fields controlling user authentication/authorization, in particular for RPC accesses.
See [Interacting with a node](clientrpc.md) for details.
If provided, node will start internal SSH server which will provide a management shell.
It uses the same credentials and permissions as RPC subsystem.
It has one required parameter.The port to start SSH server on e.g. `sshd { port = 2222 }`.*Default:* not definedInternal option.**Important: Please do not change.***Default:* 60000 millisecondsAn optional map of additional system properties to be set when launching via `corda.jar` only.
Keys and values of the map should be strings. e.g. `systemProperties = { visualvm.display.name = FooBar }`*Default:* not definedOptionally specify how much memory should be used for caching of ledger transactions in memory.*Default:* 8 MB plus 5% of all heap memory above 300MB.CRL distribution point (i.e. URL) for the TLS certificate.
Default value is NULL, which indicates no CRL availability for the TLS certificate.**Important: This needs to be set if crlCheckSoftFail is false (i.e. strict CRL checking is on).***Default:* NULLCRL issuer (given in the X500 name format) for the TLS certificate.
Default value is NULL, which indicates that the issuer of the TLS certificate is also the issuer of the CRL.**Important: If this parameter is set then `tlsCertCrlDistPoint` needs to be set as well.***Default:* NULLThe password to unlock the Trust store file (`<workspace>/certificates/truststore.jks`) containing the Corda network root certificate.
This is the non-secret value for the development certificates automatically generated during the first node run.*Default:* trustpassIf set to true, the node will use a native SSL implementation for TLS rather than the JVM SSL. The native SSL library currently shipped with
Corda Enterprise is BoringSsl. The default is to use JVM SSL, i.e. the flag being set to `false`.Internal option.**Important: Please do not change.***Default:* falseInternal option.**Important: Please do not change.***Default:* InMemory
## Reference.conf

A set of default configuration options are loaded from the built-in resource file `/node/src/main/resources/reference.conf`.
This file can be found in the `:node` gradle module of the [Corda repository](https://github.com/corda/corda).
Any options you do not specify in your own `node.conf` file will use these defaults.

Here are the contents of the `reference.conf` file:

```none
emailAddress = "admin@company.com"
keyStorePassword = "cordacadevpass"
trustStorePassword = "trustpass"
useOpenSsl = false
additionalP2PAddresses = []
crlCheckSoftFail = true
database = {
    transactionIsolationLevel = "REPEATABLE_READ"
    exportHibernateJMXStatistics = "false"
}
dataSourceProperties = {
    dataSourceClassName = org.h2.jdbcx.JdbcDataSource
    dataSource.url = "jdbc:h2:file:"${baseDirectory}"/persistence;DB_CLOSE_ON_EXIT=FALSE;WRITE_DELAY=0;LOCK_TIMEOUT=10000"
    dataSource.user = sa
    dataSource.password = ""
}
database = {
    transactionIsolationLevel = "REPEATABLE_READ"
    exportHibernateJMXStatistics = "false"
}

useTestClock = false
verifierType = InMemory
enterpriseConfiguration = {
    mutualExclusionConfiguration = {
        on = false
        updateInterval = 20000
        waitInterval = 40000
    }
    tuning = {
        flowThreadPoolSize = 1
        rpcThreadPoolSize = 4
        maximumMessagingBatchSize = 256
        p2pConfirmationWindowSize = 1048576
        brokerConnectionTtlCheckIntervalMs = 20
    }
    useMultiThreadedSMM = true
    enableCacheTracing = false
    traceTargetDirectory = ${baseDirectory}"/logs/traces"
}
rpcSettings = {
    useSsl = false
    standAloneBroker = false
}
flowTimeout {
    timeout = 30 seconds
    maxRestartCount = 6
    backoffBase = 1.8
}
jmxReporterType = JOLOKIA
keyStorePassword = "cordacadevpass"
lazyBridgeStart = true
rpcSettings = {
    useSsl = false
    standAloneBroker = false
}
trustStorePassword = "trustpass"
useTestClock = false
verifierType = InMemory

```

[reference.conf](https://github.com/corda/enterprise/blob/release/ent/4.3.1/node/src/main/resources/reference.conf)


## Configuration examples

General node configuration file for hosting the IRSDemo services

```none
myLegalName = "O=Bank A,L=London,C=GB"
keyStorePassword = "cordacadevpass"
trustStorePassword = "trustpass"
crlCheckSoftFail = true
dataSourceProperties {
    dataSourceClassName = org.h2.jdbcx.JdbcDataSource
    dataSource.url = "jdbc:h2:file:"${baseDirectory}"/persistence"
    dataSource.user = sa
    dataSource.password = ""
}
p2pAddress = "my-corda-node:10002"
rpcSettings {
    useSsl = false
    standAloneBroker = false
    address = "my-corda-node:10003"
    adminAddress = "my-corda-node:10004"
}
rpcUsers = [
    { username=user1, password=letmein, permissions=[ StartFlow.net.corda.protocols.CashProtocol ] }
]
devMode = true

```

[example-node.conf](https://github.com/corda/enterprise/blob/release/ent/4.3.1/docs/source/example-code/src/main/resources/example-node.conf)

```none
myLegalName = "O=Notary Service,OU=corda,L=London,C=GB"
keyStorePassword = "cordacadevpass"
trustStorePassword = "trustpass"
p2pAddress = "localhost:12345"
rpcSettings {
    useSsl = false
    standAloneBroker = false
    address = "my-corda-node:10003"
    adminAddress = "my-corda-node:10004"
}
notary {
    validating = false
}
compatibilityZoneURL : "https://cz.corda.net"
enterpriseConfiguration = {
    tuning = {
        rpcThreadPoolSize = 16
        flowThreadPoolSize = 256
    }
}
devMode = false
networkServices {
    doormanURL = "https://cz.example.com"
    networkMapURL = "https://cz.example.com"
}
```

Configuring a node where the Corda Compatibility Zone’s registration and Network Map services exist on different URLs

```none
myLegalName = "O=Bank A,L=London,C=GB"
keyStorePassword = "cordacadevpass"
trustStorePassword = "trustpass"
crlCheckSoftFail = true
dataSourceProperties {
    dataSourceClassName = org.h2.jdbcx.JdbcDataSource
    dataSource.url = "jdbc:h2:file:"${baseDirectory}"/persistence"
    dataSource.user = sa
    dataSource.password = ""
}
p2pAddress = "my-corda-node:10002"
rpcSettings {
    useSsl = false
    standAloneBroker = false
    address = "my-corda-node:10003"
    adminAddress = "my-corda-node:10004"
}
rpcUsers = [
    { username=user1, password=letmein, permissions=[ StartFlow.net.corda.protocols.CashProtocol ] }
]
devMode = false
networkServices {
    doormanURL = "https://registration.example.com"
    networkMapURL = "https://cz.example.com"
}

```

[example-node-with-networkservices.conf](https://github.com/corda/enterprise/blob/release/ent/4.3.1/docs/source/example-code/src/main/resources/example-node-with-networkservices.conf)



## Generating a public key hash

This section details how a public key hash can be extracted and generated from a signed CorDapp. This is required for a select number of
configuration properties.

Below are the steps to generate a hash for a CorDapp signed with a RSA certificate. A similar process should work for other certificate types.



* Extract the contents of the signed CorDapp jar.
* Run the following command (replacing the < > variables):

```none
openssl pkcs7 -in <extract_signed_jar_directory>/META-INF/<signature_to_hash>.RSA -print_certs -inform DER -outform DER \
| openssl x509 -pubkey -noout \
| openssl rsa -pubin -outform der | openssl dgst -sha256
```



* Copy the public key hash that is generated and place it into the required location (e.g. in `node.conf`).


