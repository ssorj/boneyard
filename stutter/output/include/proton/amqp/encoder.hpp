namespace proton {
namespace amqp {

class encoder {
  public:
    encoder() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}