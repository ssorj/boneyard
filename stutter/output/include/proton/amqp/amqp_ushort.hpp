namespace proton {
namespace amqp {

class amqp_ushort {
  public:
    amqp_ushort() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}