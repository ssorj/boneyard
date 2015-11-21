namespace proton {
namespace internal {

class counted {
  public:
    counted() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}