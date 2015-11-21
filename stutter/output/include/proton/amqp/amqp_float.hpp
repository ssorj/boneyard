namespace proton {
namespace amqp {

class amqp_float {
  public:
    amqp_float() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}