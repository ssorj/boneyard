namespace proton {
namespace amqp {

class decode_error {
  public:
    decode_error() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}