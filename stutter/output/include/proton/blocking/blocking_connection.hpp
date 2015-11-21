namespace proton {
namespace blocking {

class blocking_connection {
  public:
    blocking_connection() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}