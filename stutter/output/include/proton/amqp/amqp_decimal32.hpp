namespace proton {
namespace amqp {

class amqp_decimal32 {
  public:
    amqp_decimal32() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}