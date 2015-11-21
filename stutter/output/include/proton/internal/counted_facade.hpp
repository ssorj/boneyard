namespace proton {
namespace internal {

class counted_facade {
  public:
    counted_facade() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
}