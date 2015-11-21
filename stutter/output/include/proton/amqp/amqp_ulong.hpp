namespace proton {
namespace amqp {

class amqp_ulong {
  public:
    amqp_ulong() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}