namespace proton {
namespace amqp {

class amqp_char {
  public:
    amqp_char() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}