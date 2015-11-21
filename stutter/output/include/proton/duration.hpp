namespace proton {

class duration {
  public:
    duration() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}