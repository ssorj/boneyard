namespace proton {
namespace amqp {

class amqp_decimal128 {
  public:
    amqp_decimal128() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}