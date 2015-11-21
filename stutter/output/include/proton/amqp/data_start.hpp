namespace proton {
namespace amqp {

class data_start {
  public:
    data_start() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}