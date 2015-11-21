namespace proton {
namespace amqp {

class amqp_uuid {
  public:
    amqp_uuid() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}