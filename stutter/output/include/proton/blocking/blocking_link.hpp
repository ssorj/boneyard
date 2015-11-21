namespace proton {
namespace blocking {

class blocking_link {
  public:
    blocking_link() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}