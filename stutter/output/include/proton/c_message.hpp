namespace proton {

class c_message {
  public:
    c_message() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}