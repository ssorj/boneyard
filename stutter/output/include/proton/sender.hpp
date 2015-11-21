namespace proton {

class sender {
  public:
    sender() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}