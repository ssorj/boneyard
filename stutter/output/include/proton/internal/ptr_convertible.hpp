namespace proton {
namespace internal {

class ptr_convertible {
  public:
    ptr_convertible() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}