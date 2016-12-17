/**
 * Thrift types:
 *
 *  bool        Boolean, one byte
 *  byte        Signed byte
 *  i16         Signed 16-bit integer
 *  i32         Signed 32-bit integer
 *  i64         Signed 64-bit integer
 *  double      64-bit floating point value
 *  string      String
 *  binary      Blob (byte array)
 *  map<t1,t2>  Map from one type to another
 *  list<t1>    Ordered list of one type
 *  set<t1>     Set of unique elements of one type
 *
 */


/**
 * Thrift files can reference other Thrift files to include common struct
 * and service definitions. These are found using the current path, or by
 * searching relative to any paths specified with the -I compiler flag.
 *
 * Included objects are accessed using the name of the .thrift file as a
 * prefix. i.e. shared.SharedObject
 */
//include "shared.thrift"

/**
 * Thrift files can namespace, package, or prefix their output in various
 * target languages.
 */
namespace cpp domino
namespace py domino
namespace java domino

/**
 * Thrift also lets you define constants for use across languages. Complex
 * types and structs are specified using JSON notation.
 */
/*
const i32 INT32CONSTANT = 9853
const map<string,string> MAPCONSTANT = {'hello':'world', 'goodnight':'moon'}
*/

typedef byte MessageType

const MessageType HEART_BEAT = 1
const MessageType REGISTER = 2
const MessageType REGISTER_RESPONSE = 3
const MessageType SUBSCRIBE = 4
const MessageType SUBSCRIBE_RESPONSE = 5
const MessageType PUBLISH = 6
const MessageType PUBLISH_RESPONSE = 7
const MessageType PUSH = 8
const MessageType PUSH_RESPONSE = 9
const MessageType QUERY = 10
const MessageType QUERY_RESPONSE = 11

typedef byte ResponseCode

const ResponseCode SUCCESS = 1
const ResponseCode FAILED = 2

const byte APPEND = 0
const byte OVERWRITE = 1
const byte DELETE = 2

/**
 * Structs are the basic complex data structures. They are comprised of fields
 * which each have an integer identifier, a type, a symbolic name, and an
 * optional default value.
 *
 * Fields can be declared "optional", which ensures they will not be included
 * in the serialized output if they aren't set.  Note that this requires some
 * manual management in some languages.
 */
/*
struct Work {
  1: i32 num1 = 0,
  2: i32 num2,
  3: Operation op,
  4: optional string comment,
}
*/

/**
 * Structs can also be exceptions, if they are nasty.
 */
/*
exception InvalidOperation {
  1: i32 whatOp,
  2: string why
}
*/

/**
* Domino sends periodic heartbeats from 
* Domino Clients and Domino Server echos
*/
struct HeartBeatMessage {
 1: MessageType messageType = HEART_BEAT,
 2: string domino_udid,
 3: i64 seq_no  
}

/**
* Domino Clients must first register with 
* Domino Server. Clients can ask for a specific
* Unique Domino ID (UDID)
*/

struct RegisterMessage {
 1: MessageType messageType = REGISTER,
 2: string domino_udid_desired,
 3: i64 seq_no,
 4: string ipaddr,
 5: i16 tcpport,
 6: list<string> supported_templates 
}

struct RegisterResponseMessage {
 1: MessageType messageType = REGISTER_RESPONSE,
 2: string domino_udid,
 3: string domino_udid_assigned,
 4: i64 seq_no,
 5: ResponseCode responseCode,
 6: optional list<string> comments
}

struct SubscribeMessage {
 1: MessageType messageType = SUBSCRIBE,
 2: string domino_udid,
 3: i64 seq_no,
 4: byte template_op, 
 5: list<string> supported_template_types,
 6: optional byte label_op,
 7: optional list<string> labels
}

struct SubscribeResponseMessage {
 1: MessageType messageType = SUBSCRIBE_RESPONSE,
 2: string domino_udid,
 3: i64 seq_no,
 4: ResponseCode responseCode,
 5: optional list<string> comments
}

struct PublishMessage {
 1: MessageType messageType = PUBLISH,
 2: string domino_udid,
 3: i64 seq_no,
 4: string template_type,
 5: list<string> template,
 6: optional string template_UUID
}

struct PublishResponseMessage {
 1: MessageType messageType = PUBLISH_RESPONSE,
 2: string domino_udid,
 3: i64 seq_no,
 4: ResponseCode responseCode,
 5: string template_UUID,
 6: optional list<string> comments
}

struct PushMessage {
 1: MessageType messageType = PUSH,
 2: string domino_udid,
 3: i64 seq_no,
 4: string template_type,
 5: list<string> template,
 6: string template_UUID
}

struct PushResponseMessage {
 1: MessageType messageType = PUSH_RESPONSE,
 2: string domino_udid,
 3: i64 seq_no,
 4: ResponseCode responseCode,
 5: optional list<string> comments
}

struct QueryMessage{
 1: MessageType messageType = QUERY,
 2: string domino_udid,
 3: i64 seq_no,
 4: list<string> queryString,
 5: optional string template_UUID 
}

struct QueryResponseMessage{
 1: MessageType messageType = QUERY_RESPONSE,
 2: string domino_udid,
 3: i64 seq_no,
 4: ResponseCode responseCode,
 5: optional list<string> queryResponse
}

service Communication {

  /**
   * A method definition looks like C code. It has a return type, arguments,
   * and optionally a list of exceptions that it may throw. Note that argument
   * lists and exception lists are specified using the exact same syntax as
   * field lists in struct or exception definitions.
   */

   //void ping(),
   

   HeartBeatMessage d_heartbeat(1:HeartBeatMessage msg),
   RegisterResponseMessage d_register(1:RegisterMessage msg),
   SubscribeResponseMessage d_subscribe(1:SubscribeMessage msg),
   PublishResponseMessage d_publish(1:PublishMessage msg),     
   PushResponseMessage d_push(1:PushMessage msg),
   QueryResponseMessage d_query(1:QueryMessage msg)
}
