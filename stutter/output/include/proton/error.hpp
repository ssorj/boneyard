namespace proton {

class error {
  public:
    error() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}