namespace proton {

class transport {
  public:
    transport() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}