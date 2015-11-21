namespace proton {
namespace amqp {

class amqp_double {
  public:
    amqp_double() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}