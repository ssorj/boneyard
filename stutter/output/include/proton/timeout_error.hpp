namespace proton {

class timeout_error {
  public:
    timeout_error() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}