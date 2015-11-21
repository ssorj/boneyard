namespace proton {
namespace amqp {

class data {
  public:
    data() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}