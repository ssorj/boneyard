namespace proton {
namespace amqp {

class data_value {
  public:
    data_value() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}