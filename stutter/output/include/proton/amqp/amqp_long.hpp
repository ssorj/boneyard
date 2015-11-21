namespace proton {
namespace amqp {

class amqp_long {
  public:
    amqp_long() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}