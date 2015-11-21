namespace proton {
namespace amqp {

class amqp_uint {
  public:
    amqp_uint() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}