namespace proton {
namespace amqp {

class amqp_timestamp {
  public:
    amqp_timestamp() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}