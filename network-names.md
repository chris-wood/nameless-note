# Introduction

Names in CCN are hierarchical URIs formatted according to the CCNx URI naming scheme [1]. 
The names are carried verbatim in both Interests and Content Objects (with the exception
of nameless objects) [2]. In this note, we make a case for a distinguished type of 
name in CCN wherein *application names* formatted according to [1] are transformed to 
*network names* that are carried in network packets. In this memo, we present the 
motivation for this new type of name and provide one transformation scheme to map
application to network names. We also discuss the forwarder implications and necessary
changes to the request and response matching algorithm. 

[1] LCI
[2] spcs

# Motivation

Currently, the only utility CCN names in Interests afford to the network (i.e., forwarders) 
is to serve as a locator for the desired Content Object. The semantic meaning of a name,
as decided by the application, is of no consequence to a forwarder. Names are opaque 
locators used to route Interests towards some authoritative source for the corresponding
Content Objects. Names in Content Objects are only used to match against a PIT entry to 
forward the message to downstream forwarders. In summary, application semantics have
no use in the data plane of the network. Thus, the application representation of a name
is not needed to enable messages to be correctly forwarded. We therefore seek an
alternative representation that is more friendly to the network. 

# Network Names

Let N = [N1, N2, ..., Nk] be a CCN name as per [1] with k name segments. For example,
the name 

~~~
    /edu/uci/ics/woodc1
~~~

is equivalent to the vector

~~~
    [edu, uci, ics, woodc1]
~~~

According to the latest CCN specifications [1], an Interest carrying this name 
would have the following TLV-encoded name in the Interest packet. (We use
S-expressions with the length field omitted for simplicity of presentation.)

~~~
(T_NAME 
    (T_NAMESEGMENT "edu")
    (T_NAMESEGMENT "uci")
    (T_NAMESEGMENT "ics")
    (T_NAMESEGMENT "woodc1")
)
~~~

In the proposed network name scheme, each name segment would replaced
by a hash digest. Specifically, the i-th name segment will be replaced
with a hash digest based on the 1,2,...,i name segments. Formally, we 
denote this as follows:

~~~
N1' = H(N1)
N2' = H(N1 || N2)
N3' = H(N1 || N2 || N3)
...
Ni' = H(N1 || ... || Ni)
...
Nk' = H(N1 || ... || Nk)
~~~

H is a hash function which we will define later. Using this construction,
the network name N' for a given application name N is represented as 
N' = [N1', N2', ..., Nk']. 

In addition to this network name, we also require that packets with names
carry a *name fingerprint* Np, computed as follows:

~~~
    Np = CRH(N)
~~~

where CRH is a collision resistant hash function such as SHA256. 

With a suitably chosen H, the relationship between N and N' forms a bijection.

## Hash Function Criteria

Since the name is only used for forwarding purposes, it is not required that
H be a cryptographic hash function. However, it is required for the name fingerprint
function to be a cryptography hash function. We mandate that this function be the
same of that which is used to compute the ContentObjectHashRestriction that 
is specified in [2]. 

## Packet Format

The network name and fingerprint are represnted in the packets as follows.

~~~
(T_NAME 
    (T_NAMESEGMENT N1')
    ...
    (T_NAMESEGMENT N2')
    (T_NAMEFINGERPRINT Np)
)
~~~

Contrary to the current encoding outlined in [2], network names have a 
fixed size based on the H. Therefore, we do not need to encode the length
of in each name segment block. This saves 2 bytes on average for each
name component.

In particular, let D be the digest size for H and Dp be the fingerprint
size of CRH. For a name of length L, the number of name segments |N'| can 
computed as:

~~~
    |N'| = (L - Dp) / (D + 2)   # 2 is for the T byte in each segment
~~~

The byte offset Bi for the i-th name segment Ni' is computed as:

~~~
    Bi = (D + 2) * i
~~~

# Forwarder Implications

Network names can be used for routing just as standard application names are used
in [2]. FIBs must be populated with network names manually or by the routing protocol. 
However, what does change is what is stored in the FIB and how Content Object responses
are matched to Interest requests. Currently, Content Objects with names only match
Interests with names if their names are identical. Therefore, when matching a Content
Object with an Interest stored in a PIT entry, a match is only said to occur if
the Interest name fingerprint matches the Content Object name fingerprint. Since these
are computed by CRH (from which collisions occur with negligible probability), this
is no different from comparing the standard application names based on exact match. 

# Invertible Network Names

Since we use a hash function to compute N' and Np, one concern is that N would not
be recoverable since hash functions are (in this context) one-way functions. 
However, consider the cases when one might need to recover N from N' and Np. 
Inversion is only necessary when there's application data in the name, i.e., 
there is some data that the producer needs to use to produce a result. Were
this not the case then an Interest could be satisfied by a network cache. This
implies that (a) the producer already generated the *same* content for another
consumer who issued the *same request* and (b) the result will not change from
the producer (assuming identical requests yield identical response). 
Thus, we conclude that application data should *not* exist in the name and should
reside in the Paylad of an Interest. The Payload ID, which is the hash of the Payload
field in an Interest, is still reflected in the name N and N', and therefore also Np, 
so as to give N' sufficient randomness to avoid being satisfied by a cache. 

In summary, we conclude by observing that Interests convey one of two requests:

1. Requests for content that already exists. The name is the complete locator
and identifier of the content.
2. Requests for content that will be generated on-demand by the producer. The name
is only the locator for the content and the Interest Payload contains data to 
be used by the producer to provide the content. 

Our network naming scheme permits both types of requests while providing better
separation between locators and identifiers. 

# Experimental Analysis

TODO: run the code to determine how much we save...
TODO: compute entropy of URIs as they exist today...
