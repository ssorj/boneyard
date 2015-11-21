namespace proton {
namespace amqp {

class amqp_null {
  public:
    amqp_null() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}