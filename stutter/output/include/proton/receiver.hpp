namespace proton {

class receiver {
  public:
    receiver() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}