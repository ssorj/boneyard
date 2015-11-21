namespace proton {
namespace amqp {

class amqp_string {
  public:
    amqp_string() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}