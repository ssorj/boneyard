namespace proton {
namespace amqp {

class encode_error {
  public:
    encode_error() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}