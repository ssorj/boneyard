namespace proton {
namespace amqp {

class amqp_binary {
  public:
    amqp_binary() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}