namespace proton {
namespace amqp {

class amqp_decimal64 {
  public:
    amqp_decimal64() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}