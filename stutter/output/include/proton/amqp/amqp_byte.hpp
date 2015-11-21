namespace proton {
namespace amqp {

class amqp_byte {
  public:
    amqp_byte() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}