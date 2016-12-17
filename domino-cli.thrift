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


namespace cpp dominoCLI
namespace py dominoCLI
namespace java dominoCLI


/**
* Domino sends periodic heartbeats from 
* Domino Clients and Domino Server echos
*/
struct CLIMessage {
 1: list<string> CLI_input
}

struct CLIResponse {
 1: list<string> CLI_response
}

service DominoClientCLI {

   CLIResponse d_CLI(1:CLIMessage msg),
}
