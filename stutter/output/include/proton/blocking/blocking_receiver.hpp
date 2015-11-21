namespace proton {
namespace blocking {

class blocking_receiver {
  public:
    blocking_receiver() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}