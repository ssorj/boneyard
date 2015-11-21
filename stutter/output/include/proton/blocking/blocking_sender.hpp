namespace proton {
namespace blocking {

class blocking_sender {
  public:
    blocking_sender() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}