namespace proton {
namespace amqp {

class decoder {
  public:
    decoder() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}