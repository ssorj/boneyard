namespace proton {

class event {
  public:
    event() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}