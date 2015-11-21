namespace proton {
namespace internal {

class facade {
  public:
    facade() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}