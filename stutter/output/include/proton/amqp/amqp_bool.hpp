namespace proton {
namespace amqp {

class amqp_bool {
  public:
    amqp_bool() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}