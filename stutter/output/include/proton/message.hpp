namespace proton {

class message {
  public:
    message() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}