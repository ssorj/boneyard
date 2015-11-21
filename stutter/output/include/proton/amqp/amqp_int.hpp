namespace proton {
namespace amqp {

class amqp_int {
  public:
    amqp_int() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}