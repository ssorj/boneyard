namespace proton {
namespace amqp {

class amqp_short {
  public:
    amqp_short() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}