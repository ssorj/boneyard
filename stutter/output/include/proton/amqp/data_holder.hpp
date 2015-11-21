namespace proton {
namespace amqp {

class data_holder {
  public:
    data_holder() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}