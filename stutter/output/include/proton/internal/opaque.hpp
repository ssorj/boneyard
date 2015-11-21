namespace proton {
namespace internal {

class opaque {
  public:
    opaque() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}